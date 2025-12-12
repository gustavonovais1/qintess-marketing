import argparse
import re
import os
import json
from playwright.sync_api import sync_playwright
from .auth import create_context
from .profile import fetch_profile_data, click_by_href, click_company_contents, click_export, click_date_range, click_date_range_custom, fill_date_range_current_month, click_update, click_export_confirm
from .ingest import ingest_downloads

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-url")
    parser.add_argument("--storage", default="storage_state.json")
    parser.add_argument("--target-href")
    parser.add_argument("--company-href")
    parser.add_argument("--company-name")
    parser.add_argument("--open-contents", action="store_true")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--open-date-range", action="store_true")
    parser.add_argument("--to-updates", action="store_true")
    parser.add_argument("--analytics-segment", default="updates")
    args = parser.parse_args()
    with sync_playwright() as p:
        browser = None
        context = None
        try:
            browser, context = create_context(p, args.storage)
            page = context.new_page()
            default_company = os.environ.get("DEFAULT_COMPANY_HREF") or "/company/64618175/admin/"
            segments_env = os.environ.get("DEFAULT_SEGMENTS") or "updates,visitors,followers,competitors"
            segments = [s.strip().strip('/') for s in segments_env.split(',') if s.strip()]

            comp_href = args.company_href or default_company

            if comp_href:
                base = "https://www.linkedin.com" + comp_href
                for seg in segments:
                    target = base + "analytics/" + seg + "/"
                    page.goto(target)
                    try:
                        page.wait_for_url(re.compile(r"https://www\\.linkedin\\.com/company/\\d+/admin/analytics/" + re.escape(seg) + r"/?"), timeout=60000)
                    except Exception:
                        pass
                    click_date_range(page)
                    click_date_range_custom(page)
                    ok, s, e = fill_date_range_current_month(page)
                    click_update(page)
                    click_export(page)
                    base_name = f"linkedin_{seg}_{s.replace('/', '-')}_{e.replace('/', '-')}"
                    click_export_confirm(page, base_name)
                try:
                    downloads_dir = os.environ.get("DOWNLOADS_DIR") or "/app/linkedin/downloads"
                except Exception:
                    downloads_dir = "/app/linkedin/downloads"
                try:
                    ingest_downloads(downloads_dir)
                except Exception:
                    pass
                if args.open_contents:
                    c_url = click_company_contents(page)
                    if c_url and page.url != c_url:
                        page.goto(c_url)
                data = {"navigated_to": page.url}
            elif args.target_href:
                url = click_by_href(page, args.target_href)
                if url:
                    data = fetch_profile_data(page, url)
                else:
                    data = {}
            else:
                if args.profile_url:
                    data = fetch_profile_data(page, args.profile_url)
                else:
                    page.goto("https://www.linkedin.com/feed/")
                    data = {"navigated_to": page.url}
            print(json.dumps(data, ensure_ascii=False))
        finally:
            if context:
                context.close()
            if browser:
                browser.close()

if __name__ == "__main__":
    main()