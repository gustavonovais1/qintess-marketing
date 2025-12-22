from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest
from typing import List, Optional, Dict, Tuple
from datetime import date as _date
import os
from core.db import Base, engine, get_session
from models.models_google_analytics import (
    GAUsers, GAEngagement, GAEvents, GAContent, GAEcommerce,
    GAAds, GAPromotions
)

class GA4Service:
    PRESETS = {
        "users": {
            "metrics": [
                "activeUsers",
                "newUsers",
                "totalUsers",
                "active1DayUsers",
                "active7DayUsers",
                "active28DayUsers",
                "dauPerMau",
                "dauPerWau",
                "wauPerMau",
            ],
            "dimensions": ["date", "country", "deviceCategory"],
        },
        "engagement": {
            "metrics": [
                "engagedSessions",
                "engagementRate",
                "averageSessionDuration",
                "userEngagementDuration",
                "eventsPerSession",
                "sessionKeyEventRate",
                "userKeyEventRate",
                "scrolledUsers",
            ],
            "dimensions": ["date", "deviceCategory", "country"],
        },
        "events": {
            "metrics": ["eventCount", "eventCountPerUser", "eventValue", "keyEvents"],
            "dimensions": ["date", "eventName", "pagePath"],
        },
        "content": {
            "metrics": [
                "screenPageViews",
                "screenPageViewsPerSession",
                "screenPageViewsPerUser",
                "bounceRate",
            ],
            "dimensions": ["date", "pageTitle", "pagePath"],
        },
        "ecommerce": {
            "metrics": [
                "ecommercePurchases",
                "purchaseRevenue",
                "grossPurchaseRevenue",
                "totalRevenue",
                "transactions",
                "transactionsPerPurchaser",
                "itemsPurchased",
                "itemsViewed",
                "itemViewEvents",
                "itemsAddedToCart",
                "addToCarts",
                "itemsCheckedOut",
                "checkouts",
                "refundAmount",
                "taxAmount",
                "shippingAmount",
                "itemRevenue",
                "itemDiscountAmount",
                "grossItemRevenue",
                "averagePurchaseRevenue",
                "averagePurchaseRevenuePerPayingUser",
                "averagePurchaseRevenuePerUser",
                "averageRevenuePerUser",
                "cartToViewRate",
                "purchaseToViewRate",
                "purchaserRate",
                "firstTimePurchasers",
                "firstTimePurchaserRate",
                "firstTimePurchasersPerNewUser",
            ],
            "dimensions": ["date", "itemId", "itemName", "itemCategory", "sessionDefaultChannelGroup"],
        },
        "ads": {
            "metrics": [
                "advertiserAdClicks",
                "advertiserAdImpressions",
                "advertiserAdCost",
                "advertiserAdCostPerClick",
                "advertiserAdCostPerKeyEvent",
                "totalAdRevenue",
                "returnOnAdSpend",
                "publisherAdClicks",
                "publisherAdImpressions",
            ],
            "dimensions": ["date", "adUnitName", "adFormat", "adSourceName", "campaignName", "campaignId", "sessionDefaultChannelGroup"],
        },
        "promotions": {
            "metrics": [
                "promotionViews",
                "promotionClicks",
                "itemPromotionClickThroughRate",
                "itemsClickedInPromotion",
                "itemsViewedInPromotion",
                "itemListViewEvents",
                "itemListClickEvents",
                "itemListClickThroughRate",
                "itemsClickedInList",
            ],
            "dimensions": ["date", "sessionDefaultChannelGroup"],
        },
        "search": {
            "metrics": [
                "organicGoogleSearchClicks",
                "organicGoogleSearchImpressions",
                "organicGoogleSearchClickThroughRate",
                "organicGoogleSearchAveragePosition",
            ],
            "dimensions": ["date", "country", "pagePath"],
        },
    }
    def __init__(self, property_id: str):
        self.property_id = property_id
        self.client = BetaAnalyticsDataClient()

    def list_presets(self) -> List[str]:
        return list(self.PRESETS.keys())

    def suggest_dimensions_for_metrics(self, metrics: List[str]) -> List[str]:
        dims: List[str] = []
        seen = set()
        def add(d: str):
            if d not in seen:
                seen.add(d)
                dims.append(d)
        add("date")
        for m in metrics:
            for p in self.PRESETS.values():
                if m in p["metrics"]:
                    for d in p["dimensions"]:
                        add(d)
        return dims if dims else ["date"]

    def _camel_to_snake(self, name: str) -> str:
        out = []
        for ch in name:
            if ch.isupper():
                out.append("_")
                out.append(ch.lower())
            else:
                out.append(ch)
        s = "".join(out).strip("_")
        s = s.replace("__", "_")
        return s

    def _parse_date_value(self, d: Optional[str], fallback: str):
        if not d:
            y, m, dd = [int(x) for x in fallback.split("-")]
            return _date(y, m, dd)
        ds = d.strip()
        if len(ds) == 8 and ds.isdigit():
            return _date(int(ds[0:4]), int(ds[4:6]), int(ds[6:8]))
        try:
            y, m, dd = [int(x) for x in ds.split("-")]
            return _date(y, m, dd)
        except Exception:
            return None

    def _to_number(self, name: str, value: str):
        if value is None or value == "":
            return None
        lname = name.lower()
        try:
            if any(k in lname for k in ["rate", "per", "average", "revenue", "amount", "discount"]):
                return float(value)
            if "duration" in lname:
                return int(float(value))
            if "." in value or "e" in value.lower():
                return float(value)
            return int(value)
        except Exception:
            try:
                return float(value)
            except Exception:
                return None

    def _upsert_rows(self, model_cls, key_dims: List[str], rows: List[dict], start_date: str, end_date: str):
        s = get_session()
        try:
            for row in rows:
                dt = self._parse_date_value(row.get("date"), end_date)
                dim_values: Dict[str, Optional[str]] = {}
                for d in key_dims:
                    ga_key = d if d in row else None
                    if not ga_key:
                        for k in row.keys():
                            if self._camel_to_snake(k) == d:
                                ga_key = k
                                break
                    dim_values[d] = row.get(ga_key) if ga_key else None
                q = s.query(model_cls).filter(
                    model_cls.property_id == self.property_id,
                    model_cls.date == dt,
                )
                for k, v in dim_values.items():
                    q = q.filter(getattr(model_cls, k) == v)
                existing = q.first()
                if existing:
                    target = existing
                else:
                    target = model_cls(property_id=self.property_id, date=dt)
                    for k, v in dim_values.items():
                        setattr(target, k, v)
                    s.add(target)
                for mk, mv in row.items():
                    sk = self._camel_to_snake(mk)
                    if sk == "date":
                        continue
                    if hasattr(model_cls, sk):
                        setattr(target, sk, self._to_number(mk, mv) if isinstance(mv, str) else mv)
            s.commit()
        finally:
            s.close()

    def _chunked(self, seq: List[str], n: int):
        for i in range(0, len(seq), n):
            yield seq[i:i+n]

    def _validate_subset(self, items: List[str], allowed: List[str], what: str):
        bad = [x for x in items if x not in allowed]
        if bad:
            raise ValueError(f"{what} inválidos: {bad}. Permitidos: {allowed}")

    def get_active_users_last_7_days(self) -> int:
        if not self.property_id:
            raise ValueError("GA4_PROPERTY_ID ausente no ambiente")
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
            metrics=[Metric(name="activeUsers")],
        )

        response = self.client.run_report(request)

        if not response.rows:
            return 0

        return int(response.rows[0].metric_values[0].value)

    def run_report(
        self,
        metrics: List[str],
        dimensions: Optional[List[str]],
        start_date: str,
        end_date: str,
        limit: int = 1000,
        offset: int = 0,
    ):
        if not self.property_id:
            raise ValueError("GA4_PROPERTY_ID ausente no ambiente")
        dims_used = dimensions or self.suggest_dimensions_for_metrics(metrics)
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[Metric(name=m) for m in metrics],
            dimensions=[Dimension(name=d) for d in dims_used] if dims_used else [],
            limit=limit,
            offset=offset,
        )

        response = self.client.run_report(request)

        results: List[dict] = []

        for row in response.rows:
            record = {}

            if dims_used:
                for i, dim in enumerate(dims_used):
                    record[dim] = row.dimension_values[i].value

            for j, metric in enumerate(metrics):
                record[metric] = row.metric_values[j].value

            results.append(record)

        return {
            "metrics": metrics,
            "dimensions": dims_used,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "offset": offset,
            "row_count": len(results),
            "rows": results,
        }

    def run_preset_report(
        self,
        preset: str,
        start_date: str,
        end_date: str,
        limit: int = 1000,
        offset: int = 0,
    ):
        p = self.PRESETS.get(preset)
        if not p:
            raise ValueError("preset desconhecido")
        return self.run_report(
            metrics=p["metrics"],
            dimensions=p["dimensions"],
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

    def engagement_report(self, metrics: List[str], dimensions: List[str], start_date: str, end_date: str, limit: int, offset: int):
        result = self.run_report(metrics, dimensions, start_date, end_date, limit, offset)
        self._upsert_rows(GAEngagement, ["device_category","country"], result["rows"], start_date, end_date)
        return result

    def events_report(self, metrics: List[str], dimensions: List[str], start_date: str, end_date: str, limit: int, offset: int):
        result = self.run_report(metrics, dimensions, start_date, end_date, limit, offset)
        self._upsert_rows(GAEvents, ["event_name","page_path"], result["rows"], start_date, end_date)
        return result

    def users_report(self, metrics: List[str], dimensions: List[str], start_date: str, end_date: str, limit: int, offset: int):
        result = self.run_report(metrics, dimensions, start_date, end_date, limit, offset)
        self._upsert_rows(GAUsers, ["country","device_category"], result["rows"], start_date, end_date)
        return result

    def content_report(self, metrics: List[str], dimensions: List[str], start_date: str, end_date: str, limit: int, offset: int):
        result = self.run_report(metrics, dimensions, start_date, end_date, limit, offset)
        self._upsert_rows(GAContent, ["page_title","page_path"], result["rows"], start_date, end_date)
        return result

    def promotions_report(self, metrics: List[str], dimensions: List[str], start_date: str, end_date: str, limit: int, offset: int):
        result = self.run_report(metrics, dimensions, start_date, end_date, limit, offset)
        self._upsert_rows(GAPromotions, ["session_default_channel_group"], result["rows"], start_date, end_date)
        return result

    def ecommerce_items_report(self, metrics: List[str], dimensions: List[str], start_date: str, end_date: str, limit: int, offset: int):
        allowed_dims = ["date","itemId","itemName","itemCategory"]
        allowed_metrics = ["itemsPurchased","itemsViewed","itemViewEvents","itemsAddedToCart","itemsCheckedOut","itemRevenue","itemDiscountAmount","grossItemRevenue"]
        self._validate_subset(dimensions, allowed_dims, "dimensões")
        self._validate_subset(metrics, allowed_metrics, "métricas")
        combined: Dict[Tuple, Dict] = {}
        for chunk in self._chunked(metrics, 10):
            part = self.run_report(chunk, dimensions, start_date, end_date, limit, offset)
            rows = part.get("rows") or []
            for r in rows:
                key = tuple(r.get(d) for d in dimensions)
                if key not in combined:
                    combined[key] = {d: r.get(d) for d in dimensions}
                for mk in chunk:
                    combined[key][mk] = r.get(mk)
            self._upsert_rows(GAEcommerce, ["item_id","item_name","item_category"], rows, start_date, end_date)
        merged_rows = list(combined.values())
        return {
            "metrics": metrics,
            "dimensions": dimensions,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "offset": offset,
            "row_count": len(merged_rows),
            "rows": merged_rows,
        }

    def ecommerce_revenue_report(self, metrics: List[str], dimensions: List[str], start_date: str, end_date: str, limit: int, offset: int):
        allowed_dims = ["date","sessionDefaultChannelGroup"]
        allowed_metrics = ["ecommercePurchases","purchaseRevenue","grossPurchaseRevenue","totalRevenue","transactions","transactionsPerPurchaser","averagePurchaseRevenue","averagePurchaseRevenuePerPayingUser","averagePurchaseRevenuePerUser","averageRevenuePerUser","purchaserRate","firstTimePurchasers","firstTimePurchaserRate","firstTimePurchasersPerNewUser"]
        self._validate_subset(dimensions, allowed_dims, "dimensões")
        self._validate_subset(metrics, allowed_metrics, "métricas")
        combined: Dict[Tuple, Dict] = {}
        for chunk in self._chunked(metrics, 10):
            part = self.run_report(chunk, dimensions, start_date, end_date, limit, offset)
            rows = part.get("rows") or []
            for r in rows:
                key = tuple(r.get(d) for d in dimensions)
                if key not in combined:
                    combined[key] = {d: r.get(d) for d in dimensions}
                for mk in chunk:
                    combined[key][mk] = r.get(mk)
            self._upsert_rows(GAEcommerce, ["session_default_channel_group"], rows, start_date, end_date)
        merged_rows = list(combined.values())
        return {
            "metrics": metrics,
            "dimensions": dimensions,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "offset": offset,
            "row_count": len(merged_rows),
            "rows": merged_rows,
        }

    def ecommerce_funnel_report(self, metrics: List[str], dimensions: List[str], start_date: str, end_date: str, limit: int, offset: int):
        allowed_dims = ["date","sessionDefaultChannelGroup"]
        allowed_metrics = ["addToCarts","checkouts","ecommercePurchases","cartToViewRate","purchaseToViewRate"]
        self._validate_subset(dimensions, allowed_dims, "dimensões")
        self._validate_subset(metrics, allowed_metrics, "métricas")
        result = self.run_report(metrics, dimensions, start_date, end_date, limit, offset)
        self._upsert_rows(GAEcommerce, ["session_default_channel_group"], result["rows"], start_date, end_date)
        return result

    def ads_report(self, metrics: List[str], dimensions: List[str], start_date: str, end_date: str, limit: int, offset: int):
        allowed_dims = ["date","campaignName","campaignId"]
        allowed_metrics = ["advertiserAdClicks","advertiserAdImpressions","advertiserAdCost","advertiserAdCostPerClick"]
        self._validate_subset(dimensions, allowed_dims, "dimensões")
        self._validate_subset(metrics, allowed_metrics, "métricas")
        combined: Dict[Tuple, Dict] = {}
        for chunk in self._chunked(metrics, 10):
            part = self.run_report(chunk, dimensions, start_date, end_date, limit, offset)
            rows = part.get("rows") or []
            for r in rows:
                key = tuple(r.get(d) for d in dimensions)
                if key not in combined:
                    combined[key] = {d: r.get(d) for d in dimensions}
                for mk in chunk:
                    combined[key][mk] = r.get(mk)
            self._upsert_rows(GAAds, ["campaign_name","campaign_id"], rows, start_date, end_date)
        merged_rows = list(combined.values())
        return {
            "metrics": metrics,
            "dimensions": dimensions,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "offset": offset,
            "row_count": len(merged_rows),
            "rows": merged_rows,
        }

def _split_csv(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]

def _get_service() -> GA4Service:
    return GA4Service(property_id=os.getenv("GA4_PROPERTY_ID"))

def engagement_report(metrics: str, dimensions: str, start_date: str, end_date: str, limit: int, offset: int):
    svc = _get_service()
    return svc.engagement_report(_split_csv(metrics), _split_csv(dimensions), start_date, end_date, limit, offset)

def events_report(metrics: str, dimensions: str, start_date: str, end_date: str, limit: int, offset: int):
    svc = _get_service()
    return svc.events_report(_split_csv(metrics), _split_csv(dimensions), start_date, end_date, limit, offset)

def users_report(metrics: str, dimensions: str, start_date: str, end_date: str, limit: int, offset: int):
    svc = _get_service()
    return svc.users_report(_split_csv(metrics), _split_csv(dimensions), start_date, end_date, limit, offset)

def content_report(metrics: str, dimensions: str, start_date: str, end_date: str, limit: int, offset: int):
    svc = _get_service()
    return svc.content_report(_split_csv(metrics), _split_csv(dimensions), start_date, end_date, limit, offset)

def promotions_report(metrics: str, dimensions: str, start_date: str, end_date: str, limit: int, offset: int):
    svc = _get_service()
    return svc.promotions_report(_split_csv(metrics), _split_csv(dimensions), start_date, end_date, limit, offset)

def ecommerce_items_report(metrics: str, dimensions: str, start_date: str, end_date: str, limit: int, offset: int):
    svc = _get_service()
    return svc.ecommerce_items_report(_split_csv(metrics), _split_csv(dimensions), start_date, end_date, limit, offset)

def ecommerce_revenue_report(metrics: str, dimensions: str, start_date: str, end_date: str, limit: int, offset: int):
    svc = _get_service()
    return svc.ecommerce_revenue_report(_split_csv(metrics), _split_csv(dimensions), start_date, end_date, limit, offset)

def ecommerce_funnel_report(metrics: str, dimensions: str, start_date: str, end_date: str, limit: int, offset: int):
    svc = _get_service()
    return svc.ecommerce_funnel_report(_split_csv(metrics), _split_csv(dimensions), start_date, end_date, limit, offset)

def ads_report(metrics: str, dimensions: str, start_date: str, end_date: str, limit: int, offset: int):
    svc = _get_service()
    return svc.ads_report(_split_csv(metrics), _split_csv(dimensions), start_date, end_date, limit, offset)
