import os
import re
from datetime import datetime, timedelta
from playwright.sync_api import Page

def fetch_profile_data(page: Page, url: str):
    page.goto(url)
    page.wait_for_load_state("networkidle")
    data = {"name": "", "headline": "", "location": "", "about": ""}
    try:
        data["name"] = page.locator("h1").first.inner_text().strip()
    except Exception:
        pass
    try:
        data["headline"] = page.locator('[class*="text-body-medium"]').first.inner_text().strip()
    except Exception:
        pass
    try:
        tabs = page.locator('a[href*="about"]').first
        if tabs:
            tabs.click()
            page.wait_for_selector('section[id*="about"]')
            data["about"] = page.locator('section[id*="about"] div').first.inner_text().strip()
    except Exception:
        pass
    try:
        data["location"] = page.locator('[class*="text-body-small"]').first.inner_text().strip()
    except Exception:
        pass
    return data
    
def click_by_href(page: Page, href: str):
    page.goto("https://www.linkedin.com/feed/")
    page.wait_for_load_state("domcontentloaded")
    selectors = [f'a[href="{href}"]']
    if href.startswith("/"):
        selectors.append(f'a[href*="{href}"]')
        selectors.append(f'a[href$="{href}"]')
    else:
        selectors.append(f'a[href*="{href}"]')
    for _ in range(20):
        for s in selectors:
            loc = page.locator(s)
            if loc.count() > 0:
                try:
                    loc.first.evaluate('el => el.removeAttribute("target")')
                except Exception:
                    pass
                try:
                    loc.first.click()
                    page.wait_for_url(re.compile(r"https://www\.linkedin\.com/in/.*"), timeout=60000)
                    return page.url
                except Exception:
                    try:
                        with page.expect_popup() as popup_info:
                            loc.first.click()
                        popup = popup_info.value
                        popup.wait_for_url(re.compile(r"https://www\.linkedin\.com/in/.*"), timeout=60000)
                        return popup.url
                    except Exception:
                        pass
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(200)
    return ""
    
def click_company_admin(page: Page, href: str, company_name: str | None = None):
    page.goto("https://www.linkedin.com/feed/")
    page.wait_for_load_state("domcontentloaded")
    base = [f'a[href="{href}"]']
    if href.startswith("/"):
        base.append(f'a[href*="{href}"]')
        base.append(f'a[href$="{href}"]')
    else:
        base.append(f'a[href*="{href}"]')
    selectors = []
    if company_name:
        for s in base:
            selectors.append(f'{s}:has-text("{company_name}")')
    selectors.extend(base)
    for _ in range(20):
        for s in selectors:
            loc = page.locator(s)
            if loc.count() > 0:
                try:
                    loc.first.evaluate('el => el.removeAttribute("target")')
                except Exception:
                    pass
                try:
                    with page.expect_popup() as popup_info:
                        loc.first.click()
                    popup = popup_info.value
                    popup.wait_for_url(re.compile(r"https://www\.linkedin\.com/company/.*/admin/.*"), timeout=60000)
                    return popup.url
                except Exception:
                    page.wait_for_url(re.compile(r"https://www\.linkedin\.com/company/.*/admin/.*"), timeout=60000)
                    return page.url
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(200)
    return ""
def click_company_contents(page: Page):
    selectors = [
        '#org-menu-CONTENTS',
        'a[data-test-org-menu-item="CONTENTS"]',
        'a[href$="/admin/analytics/updates"]',
        'a[href*="/admin/analytics/updates"]',
    ]
    loc = None
    for s in selectors:
        c = page.locator(s)
        if c.count() > 0:
            loc = c.first
            break
    if not loc:
        by_role = page.get_by_role("link", name=re.compile(r"Conteúdo", re.I))
        if by_role.count() > 0:
            loc = by_role.first
    if not loc:
        return ""
    try:
        loc.wait_for(state="visible", timeout=30000)
    except Exception:
        pass
    try:
        loc.evaluate('el => el.removeAttribute("target")')
    except Exception:
        pass
    try:
        loc.click()
        page.wait_for_url(re.compile(r"https://www\.linkedin\.com/company/.*/admin/analytics/updates.*"), timeout=60000)
        return page.url
    except Exception:
        try:
            with page.expect_popup() as popup_info:
                loc.click()
            popup = popup_info.value
            popup.wait_for_url(re.compile(r"https://www\.linkedin\.com/company/.*/admin/analytics/updates.*"), timeout=60000)
            return popup.url
        except Exception:
            href = None
            try:
                href = loc.get_attribute("href")
            except Exception:
                pass
            if href:
                page.goto(href)
            page.wait_for_url(re.compile(r"https://www\.linkedin\.com/company/.*/admin/analytics/updates.*"), timeout=60000)
            return page.url
def click_export(page: Page):
    by_name = page.get_by_role("button", name=re.compile(r"Exportar", re.I))
    if by_name.count() > 0:
        b = by_name.first
        try:
            b.scroll_into_view_if_needed()
        except Exception:
            pass
        try:
            b.click()
        except Exception:
            try:
                b.click(force=True)
            except Exception:
                return False
        try:
            conts = [page.locator('div[role="dialog"]'), page.locator('.artdeco-modal')]
            for cont in conts:
                if cont.count() > 0:
                    try:
                        cont.first.wait_for(state='visible', timeout=8000)
                    except Exception:
                        pass
                    break
        except Exception:
            pass
        return True
    selectors = [
        'button:has(svg use[href="#download-small"])',
        'button:has(svg[data-test-icon="download-small"])',
        'button.artdeco-button--primary:has-text("Exportar")',
    ]
    for s in selectors:
        loc = page.locator(s)
        if loc.count() > 0:
            btn = loc.first
            try:
                btn.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                btn.click()
            except Exception:
                try:
                    btn.click(force=True)
                except Exception:
                    continue
            try:
                conts = [page.locator('div[role="dialog"]'), page.locator('.artdeco-modal')]
                for cont in conts:
                    if cont.count() > 0:
                        try:
                            cont.first.wait_for(state='visible', timeout=8000)
                        except Exception:
                            pass
                        break
            except Exception:
                pass
            return True
    return False
def click_date_range(page: Page):
    container = page.locator('div.artdeco-dropdown:has(button[aria-label^="Período:"])')
    btn = None
    if container.count() > 0:
        btn = container.first.locator('button.artdeco-dropdown__trigger').first
    else:
        btn = page.locator('button[aria-label^="Período:"]').first
    if btn:
        try:
            btn.wait_for(state="visible", timeout=5000)
        except Exception:
            pass
        try:
            btn.scroll_into_view_if_needed()
        except Exception:
            pass
        try:
            btn.click()
        except Exception:
            try:
                btn.focus()
                page.keyboard.press("Enter")
            except Exception:
                try:
                    btn.evaluate('el => { el.dispatchEvent(new MouseEvent("mousedown",{bubbles:true})); el.dispatchEvent(new MouseEvent("mouseup",{bubbles:true})); el.dispatchEvent(new MouseEvent("click",{bubbles:true})); }')
                except Exception:
                    try:
                        box = btn.bounding_box() or {}
                        x = box.get('x'); y = box.get('y'); w = box.get('width'); h = box.get('height')
                        if x is not None and y is not None and w and h:
                            page.mouse.click(x + w/2, y + h/2)
                    except Exception:
                        pass
        try:
            page.wait_for_function('document.querySelector("div.artdeco-dropdown__content")?.getAttribute("aria-hidden") === "false" || document.querySelector("button[aria-label^=\\"Período:\\"]")?.getAttribute("aria-expanded") === "true"', timeout=4000)
            return True
        except Exception:
            pass
    return False
def click_date_range_custom(page: Page):
    content = page.locator('div.artdeco-dropdown__content')
    try:
        content.first.wait_for(state='visible', timeout=5000)
    except Exception:
        pass
    targets = [
        page.get_by_role('button', name=re.compile(r'Personalizado', re.I)),
        page.locator('div[role="button"].artdeco-dropdown__item:has-text("Personalizado")'),
    ]
    for loc in targets:
        if loc.count() > 0:
            btn = loc.first
            try:
                btn.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                btn.click()
                return True
            except Exception:
                try:
                    btn.click(force=True)
                    return True
                except Exception:
                    continue
    return False
def fill_date_range_current_month(page: Page):
    now = datetime.now()
    end = now - timedelta(days=2)
    if end.day <= 2:
        pm = end.month - 1 if end.month > 1 else 12
        py = end.year if end.month > 1 else end.year - 1
        start = datetime(py, pm, 1)
    else:
        start = now.replace(day=1)
    if start > end:
        pm = end.month - 1 if end.month > 1 else 12
        py = end.year if end.month > 1 else end.year - 1
        start = datetime(py, pm, 1)
    s = f"{start.day:02d}/{start.month:02d}/{start.year:04d}"
    e = f"{end.day:02d}/{end.month:02d}/{end.year:04d}"
    content = page.locator('div.artdeco-dropdown__content')
    try:
        content.first.wait_for(state='visible', timeout=5000)
    except Exception:
        pass
    s_input = page.locator('input[name="rangeStart"]')
    e_input = page.locator('input[name="rangeEnd"]')
    ok = False
    if s_input.count() > 0:
        si = s_input.first
        try:
            si.scroll_into_view_if_needed()
        except Exception:
            pass
        try:
            si.click()
        except Exception:
            pass
        try:
            si.fill(s)
        except Exception:
            try:
                si.press("Control+A")
                si.type(s)
            except Exception:
                try:
                    si.evaluate('el => { el.value = ""; el.dispatchEvent(new Event("input",{bubbles:true})); el.value = "%s"; el.dispatchEvent(new Event("input",{bubbles:true})); el.dispatchEvent(new Event("change",{bubbles:true})); }' % s)
                except Exception:
                    pass
        ok = True
    if e_input.count() > 0:
        ei = e_input.first
        try:
            ei.scroll_into_view_if_needed()
        except Exception:
            pass
        try:
            ei.click()
        except Exception:
            pass
        try:
            ei.fill(e)
        except Exception:
            try:
                ei.press("Control+A")
                ei.type(e)
            except Exception:
                try:
                    ei.evaluate('el => { el.value = ""; el.dispatchEvent(new Event("input",{bubbles:true})); el.value = "%s"; el.dispatchEvent(new Event("input",{bubbles:true})); el.dispatchEvent(new Event("change",{bubbles:true})); }' % e)
                except Exception:
                    pass
        ok = True
    try:
        page.keyboard.press("Tab")
    except Exception:
        pass
    try:
        page.wait_for_timeout(300)
    except Exception:
        pass
    return ok, s, e
def click_update(page: Page):
    content = page.locator('div.artdeco-dropdown__content')
    try:
        content.first.wait_for(state='visible', timeout=5000)
    except Exception:
        pass
    targets = [
        page.get_by_role('button', name=re.compile(r'Atualizar', re.I)),
        page.locator('button.artdeco-button--primary:has-text("Atualizar")'),
    ]
    for loc in targets:
        if loc.count() > 0:
            btn = loc.first
            try:
                btn.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                btn.click()
            except Exception:
                try:
                    btn.click(force=True)
                except Exception:
                    continue
            try:
                page.wait_for_function('document.querySelector("div.artdeco-dropdown__content")?.getAttribute("aria-hidden") === "true"', timeout=4000)
            except Exception:
                pass
            try:
                page.wait_for_load_state('networkidle')
            except Exception:
                pass
            return True
    return False
    
def click_export_confirm(page: Page, custom_basename: str | None = None):
    containers = [
        page.locator('div[role="dialog"]'),
        page.locator('.artdeco-modal'),
    ]
    for c in containers:
        if c.count() > 0:
            try:
                c.first.wait_for(state='visible', timeout=5000)
            except Exception:
                pass
            by_role = c.first.get_by_role('button', name=re.compile(r'Exportar', re.I))
            if by_role.count() > 0:
                b = by_role.first
                try:
                    b.scroll_into_view_if_needed()
                except Exception:
                    pass
                try:
                    downloads_dir = os.environ.get("DOWNLOADS_DIR") or "/app/downloads"
                except Exception:
                    downloads_dir = "/app/downloads"
                try:
                    os.makedirs(downloads_dir, exist_ok=True)
                except Exception:
                    pass
                try:
                    with page.expect_download() as di:
                        b.click()
                    d = di.value
                    try:
                        suggested = getattr(d, 'suggested_filename', None) or 'export.xlsx'
                    except Exception:
                        suggested = 'export.xlsx'
                    try:
                        import os as _os
                        _, ext = _os.path.splitext(suggested)
                        if not ext:
                            ext = '.xlsx'
                    except Exception:
                        ext = '.xlsx'
                    target = os.path.join(downloads_dir, (custom_basename + ext) if custom_basename else suggested)
                    try:
                        d.save_as(target)
                    except Exception:
                        try:
                            p = d.path()
                            if p and p != target:
                                try:
                                    # best-effort move
                                    import shutil
                                    shutil.move(p, target)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    return True
                except Exception:
                    try:
                        b.click(force=True)
                        page.wait_for_load_state('networkidle')
                        return True
                    except Exception:
                        continue
            loc = c.first.locator('button.artdeco-button--primary:has-text("Exportar")')
            if loc.count() > 0:
                b = loc.first
                try:
                    b.scroll_into_view_if_needed()
                except Exception:
                    pass
                try:
                    downloads_dir = os.environ.get("DOWNLOADS_DIR") or "/app/downloads"
                except Exception:
                    downloads_dir = "/app/downloads"
                try:
                    os.makedirs(downloads_dir, exist_ok=True)
                except Exception:
                    pass
                try:
                    with page.expect_download() as di:
                        b.click()
                    d = di.value
                    try:
                        suggested = getattr(d, 'suggested_filename', None) or 'export.xlsx'
                    except Exception:
                        suggested = 'export.xlsx'
                    try:
                        import os as _os
                        _, ext = _os.path.splitext(suggested)
                        if not ext:
                            ext = '.xlsx'
                    except Exception:
                        ext = '.xlsx'
                    target = os.path.join(downloads_dir, (custom_basename + ext) if custom_basename else suggested)
                    try:
                        d.save_as(target)
                    except Exception:
                        try:
                            p = d.path()
                            if p and p != target:
                                try:
                                    import shutil
                                    shutil.move(p, target)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    return True
                except Exception:
                    try:
                        b.click(force=True)
                        page.wait_for_load_state('networkidle')
                        return True
                    except Exception:
                        continue
    by_role = page.get_by_role('button', name=re.compile(r'Exportar', re.I))
    if by_role.count() > 1:
        b = by_role.nth(1)
        try:
            b.scroll_into_view_if_needed()
        except Exception:
            pass
        try:
            downloads_dir = os.environ.get("DOWNLOADS_DIR") or "/app/downloads"
        except Exception:
            downloads_dir = "/app/downloads"
        try:
            os.makedirs(downloads_dir, exist_ok=True)
        except Exception:
            pass
        try:
            with page.expect_download() as di:
                b.click()
            d = di.value
            try:
                suggested = getattr(d, 'suggested_filename', None) or 'export.xlsx'
            except Exception:
                suggested = 'export.xlsx'
            try:
                import os as _os
                _, ext = _os.path.splitext(suggested)
                if not ext:
                    ext = '.xlsx'
            except Exception:
                ext = '.xlsx'
            target = os.path.join(downloads_dir, (custom_basename + ext) if custom_basename else suggested)
            try:
                d.save_as(target)
            except Exception:
                try:
                    p = d.path()
                    if p and p != target:
                        try:
                            import shutil
                            shutil.move(p, target)
                        except Exception:
                            pass
                except Exception:
                    pass
            return True
        except Exception:
            try:
                b.click(force=True)
                page.wait_for_load_state('networkidle')
                return True
            except Exception:
                return False
    try:
        x = page.locator('xpath=/html/body/div[4]/div/div/div[3]/button[2]')
        if x.count() > 0:
            try:
                x.first.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                downloads_dir = os.environ.get("DOWNLOADS_DIR") or "/app/downloads"
            except Exception:
                downloads_dir = "/app/downloads"
            try:
                os.makedirs(downloads_dir, exist_ok=True)
            except Exception:
                pass
            try:
                with page.expect_download() as di:
                    x.first.click()
                d = di.value
                try:
                    suggested = getattr(d, 'suggested_filename', None) or 'export.xlsx'
                except Exception:
                    suggested = 'export.xlsx'
                try:
                    import os as _os
                    _, ext = _os.path.splitext(suggested)
                    if not ext:
                        ext = '.xlsx'
                except Exception:
                    ext = '.xlsx'
                target = os.path.join(downloads_dir, (custom_basename + ext) if custom_basename else suggested)
                try:
                    d.save_as(target)
                except Exception:
                    try:
                        p = d.path()
                        if p and p != target:
                            try:
                                import shutil
                                shutil.move(p, target)
                            except Exception:
                                pass
                    except Exception:
                        pass
                return True
            except Exception:
                try:
                    x.first.click(force=True)
                    page.wait_for_load_state('networkidle')
                    return True
                except Exception:
                    pass
    except Exception:
        pass
    return False

def go_to_updates(page: Page):
    current = page.url
    if re.search(r"/admin/analytics/updates/?", current):
        return current
    m = re.search(r"(https://www\.linkedin\.com/company/\d+/admin/analytics/)(visitors|updates)/?", current)
    if m:
        target = m.group(1) + "updates/"
        if target != current:
            page.goto(target)
            page.wait_for_url(re.compile(r"https://www\.linkedin\.com/company/\d+/admin/analytics/updates/?"), timeout=60000)
        return target
    return ""