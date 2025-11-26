import os
import re
import json
from playwright.sync_api import Playwright, BrowserContext

def create_context(playwright: Playwright, storage_path: str):
    headless_env = os.environ.get("HEADLESS", "true").lower()
    headless = headless_env not in ("false", "0", "no")

    browser = playwright.chromium.launch(
        headless=headless,
        args=["--disable-blink-features=AutomationControlled"]
    )

    video_dir = os.environ.get("RECORD_VIDEO_DIR")

    if os.path.exists(storage_path):
        context = browser.new_context(
            storage_state=storage_path,
            record_video_dir=video_dir if video_dir else None,
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
            accept_downloads=True
        )
        context.set_default_timeout(60000)
        context.set_default_navigation_timeout(60000)
        return browser, context

    email = os.environ.get("INSTAGRAM_EMAIL")
    password = os.environ.get("INSTAGRAM_PASSWORD")
    try:
        print(json.dumps({"ig_env_email_present": bool(email), "ig_env_password_present": bool(password)}))
    except Exception:
        pass

    context = browser.new_context(
        record_video_dir=video_dir if video_dir else None,
        viewport={"width": 1280, "height": 900},
        ignore_https_errors=True,
        accept_downloads=True
    )
    context.set_default_timeout(60000)
    context.set_default_navigation_timeout(60000)

    page = context.new_page()
    try:
        page.add_init_script("""
            document.addEventListener('click', (e) => {
                const a = e.target && e.target.closest && e.target.closest('a');
                if (a) { a.removeAttribute('target'); }
            }, true);
        """)
    except Exception:
        pass
    try:
        page.add_init_script("""
            window.open = (url, target, features) => { if (url) { window.location.href = url; } return null; };
        """)
    except Exception:
        pass
    try:
        def popup_guard(p):
            try:
                p.close()
            except Exception:
                pass
        page.on("popup", popup_guard)
    except Exception:
        pass
    try:
        _setup_navigation_guards(context, page)
    except Exception:
        pass

    try:
        page.goto("https://www.instagram.com/accounts/login/")
    except Exception:
        try:
            page.goto("https://www.instagram.com/")
        except Exception:
            pass

    try:
        for txt in ["Permitir todos os cookies", "Permitir essenciais", "Aceitar", "Allow all cookies", "Allow essential cookies"]:
            btn = page.get_by_role("button", name=re.compile(txt, re.I)).first
            if btn and btn.count() > 0:
                try:
                    btn.click()
                    try:
                        print(json.dumps({"ig_cookie_click": txt}))
                    except Exception:
                        pass
                    break
                except Exception:
                    pass
    except Exception:
        pass

    if not email or not password:
        try:
            page.wait_for_url(re.compile(r"instagram\.com/"), timeout=300000)
        except Exception:
            pass
        try:
            context.storage_state(path=storage_path)
        except Exception:
            pass
        return browser, context

    try:
        u = page.locator('input[name="username"]').first
        p = page.locator('input[name="password"]').first
        if u.count() == 0:
            u = page.locator('input[aria-label*="utilizador"], input[aria-label*="username"], input[aria-label*="e-mail"]').first
        if p.count() == 0:
            p = page.locator('input[aria-label*="Palavra"], input[aria-label*="password"]').first
        try:
            u.wait_for(state="visible", timeout=20000)
            p.wait_for(state="visible", timeout=20000)
        except Exception:
            pass
        try:
            page.wait_for_load_state("domcontentloaded")
        except Exception:
            pass
        try:
            page.wait_for_load_state("networkidle")
        except Exception:
            pass
        try:
            ready = (u.is_visible() and p.is_visible())
            print(json.dumps({"ig_fields_ready": ready}))
        except Exception:
            pass
        try:
            u.scroll_into_view_if_needed()
            p.scroll_into_view_if_needed()
        except Exception:
            pass
        try:
            u.click()
        except Exception:
            pass
        try:
            u.fill(email)
        except Exception:
            try:
                u.press("Control+A")
                u.type(email)
            except Exception:
                try:
                    u.evaluate('el => { el.value = ""; el.dispatchEvent(new Event("input",{bubbles:true})); el.value = "%s"; el.dispatchEvent(new Event("input",{bubbles:true})); el.dispatchEvent(new Event("change",{bubbles:true})); }' % email)
                except Exception:
                    pass
        try:
            print(json.dumps({"ig_fill_username": True}))
        except Exception:
            pass
        try:
            p.click()
        except Exception:
            pass
        try:
            p.fill(password)
        except Exception:
            try:
                p.press("Control+A")
                p.type(password)
            except Exception:
                try:
                    p.evaluate('el => { el.value = ""; el.dispatchEvent(new Event("input",{bubbles:true})); el.value = "%s"; el.dispatchEvent(new Event("input",{bubbles:true})); el.dispatchEvent(new Event("change",{bubbles:true})); }' % password)
                except Exception:
                    pass
        try:
            print(json.dumps({"ig_fill_password": True}))
        except Exception:
            pass
        try:
            page.keyboard.press("Tab")
        except Exception:
            pass
    except Exception:
        pass
    try:
        page.click('button[type="submit"]')
    except Exception:
        pass

    try:
        print(json.dumps({"ig_click_submit": True}))
    except Exception:
        pass
    try:
        page.wait_for_url(re.compile(r"instagram\.com/"), timeout=120000)
    except Exception:
        pass

    try:
        context.storage_state(path=storage_path)
    except Exception:
        pass

    return browser, context

def _setup_navigation_guards(context: BrowserContext, main_page):
    def on_page(p):
        try:
            url = p.url
            if p != main_page and "instagram.com/accounts/login" in url:
                try:
                    p.close()
                except Exception:
                    pass
        except Exception:
            pass
    context.on("page", on_page)