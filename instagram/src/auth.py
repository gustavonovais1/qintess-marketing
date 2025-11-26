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
        _perform_login(page, email, password)
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

def _get_login_locators(page):
    u = page.locator('input[name="username"]').first
    p = page.locator('input[name="password"]').first
    if u.count() == 0:
        u = page.locator('input[aria-label*="utilizador"], input[aria-label*="username"], input[aria-label*="e-mail"]').first
    if p.count() == 0:
        p = page.locator('input[aria-label*="Palavra"], input[aria-label*="password"]').first
    b = page.locator('button[type="submit"]').first
    if b.count() == 0:
        b = page.get_by_role('button', name=re.compile(r'Entrar|Iniciar Sessão', re.I)).first
    return u, p, b

def _fill_input(loc, text):
    try:
        loc.fill(text)
        return True
    except Exception:
        try:
            loc.press("Control+A")
            loc.type(text)
            return True
        except Exception:
            try:
                loc.evaluate('el => { el.value = ""; el.dispatchEvent(new Event("input",{bubbles:true})); el.value = "%s"; el.dispatchEvent(new Event("input",{bubbles:true})); el.dispatchEvent(new Event("change",{bubbles:true})); }' % text)
                return True
            except Exception:
                return False

def _perform_login(page, email, password):
    attempts = 0
    while attempts < 5:
        try:
            page.wait_for_load_state("domcontentloaded")
        except Exception:
            pass
        try:
            page.wait_for_load_state("networkidle")
        except Exception:
            pass
        u, p, b = _get_login_locators(page)
        try:
            u.wait_for(state="visible", timeout=10000)
            p.wait_for(state="visible", timeout=10000)
        except Exception:
            attempts += 1
            continue
        try:
            u.scroll_into_view_if_needed(); p.scroll_into_view_if_needed()
        except Exception:
            pass
        try:
            u.click()
        except Exception:
            pass
        ok_u = _fill_input(u, email)
        try:
            print(json.dumps({"ig_fill_username": ok_u}))
        except Exception:
            pass
        try:
            p.click()
        except Exception:
            pass
        ok_p = _fill_input(p, password)
        try:
            print(json.dumps({"ig_fill_password": ok_p}))
        except Exception:
            pass
        try:
            val_u = u.input_value()
            val_p = p.input_value()
            ready = bool(val_u) and bool(val_p)
            print(json.dumps({"ig_inputs_ready": ready}))
        except Exception:
            ready = True
        try:
            if not b.is_enabled():
                b.evaluate('el => { try { el.removeAttribute("disabled"); } catch(e){} }')
        except Exception:
            pass
        clicked = False
        try:
            b.click()
            clicked = True
        except Exception:
            try:
                page.keyboard.press("Enter")
                clicked = True
            except Exception:
                pass
        try:
            print(json.dumps({"ig_submit_clicked": clicked}))
        except Exception:
            pass
        try:
            page.wait_for_url(re.compile(r"instagram\.com/"), timeout=15000)
            return
        except Exception:
            attempts += 1
            continue
    return