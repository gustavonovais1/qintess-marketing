import os
import re
import time
import json
from urllib.request import Request, urlopen
from urllib.parse import urlparse, parse_qs, unquote
from playwright.sync_api import Playwright, Page, Frame, BrowserContext


# ================================================================
# PREPARO DA PÁGINA — evita abrir aba nova (target="_blank" / window.open)
# ================================================================
def _prepare_page(page: Page):
    try:
        # Remove target="_blank" de QUALQUER link
        page.add_init_script("""
            document.addEventListener('click', (e) => {
                const a = e.target && e.target.closest && e.target.closest('a');
                if (a) {
                    a.removeAttribute('target');
                }
            }, true);
        """)

        # Força window.open a abrir NA MESMA ABA
        page.add_init_script("""
            window.open = (url, target, features) => {
                if (url) {
                    window.location.href = url;
                }
                return null;
            };
        """)
    except:
        pass

    # Tratamento de popups
    def popup_guard(popup):
        try:
            popup.wait_for_load_state("domcontentloaded")
        except:
            pass

        # Se for recaptcha → resolver normalmente
        if _recaptcha_present(popup):
            try:
                api_key = os.environ.get("ANTI_CAPTCHA_KEY")
                if api_key:
                    token = _solve_recaptcha(popup, api_key)
                    if token:
                        f = _get_captcha_frame(popup)
                        if f:
                            _try_submit_captcha_frame(f)
            except Exception as e:
                print(f"[popup] erro resolvendo recaptcha: {e}")
            return

        # Se não for recaptcha → FECHAR popup (evita aba 2)
        try:
            popup.close()
        except:
            pass

    page.on("popup", popup_guard)


# ================================================================
# CRIA CONTEXTO E LOGIN
# ================================================================
def create_context(playwright: Playwright, storage_path: str):
    headless_env = os.environ.get("HEADLESS", "true").lower()
    headless = headless_env not in ("false", "0", "no")

    browser = playwright.chromium.launch(
        headless=headless,
        args=["--disable-blink-features=AutomationControlled"]
    )

    video_dir = os.environ.get("RECORD_VIDEO_DIR")

    # -----------------------------------------
    # Se storage_state já existe → só carregar
    # -----------------------------------------
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
        try:
            downloads_dir = os.environ.get("DOWNLOADS_DIR") or "/app/downloads"
        except Exception:
            downloads_dir = "/app/downloads"
        try:
            os.makedirs(downloads_dir, exist_ok=True)
        except Exception:
            pass
        try:
            context.set_default_downloads_path(downloads_dir)
        except Exception:
            pass
        return browser, context

    # -----------------------------------------
    # Login manual (sem e-mail/senha)
    # -----------------------------------------
    email = os.environ.get("LINKEDIN_EMAIL")
    password = os.environ.get("LINKEDIN_PASSWORD")

    context = browser.new_context(
        record_video_dir=video_dir if video_dir else None,
        viewport={"width": 1280, "height": 900},
        ignore_https_errors=True,
        accept_downloads=True
    )
    context.set_default_timeout(60000)
    context.set_default_navigation_timeout(60000)
    try:
        downloads_dir = os.environ.get("DOWNLOADS_DIR") or "/app/downloads"
    except Exception:
        downloads_dir = "/app/downloads"
    try:
        os.makedirs(downloads_dir, exist_ok=True)
    except Exception:
        pass
    try:
        context.set_default_downloads_path(downloads_dir)
    except Exception:
        pass

    page = context.new_page()

    _prepare_page(page)
    _setup_navigation_guards(context, page)

    # Se não tem e-mail → login manual
    if not email or not password:
        page.goto("https://www.linkedin.com/login")

        try:
            page.wait_for_url(
                re.compile(r"linkedin\.com/(feed|company/.*|checkpoint)/"),
                timeout=300000
            )
        except:
            pass

        try:
            context.storage_state(path=storage_path)
        except:
            pass

        return browser, context

    # -----------------------------------------
    # LOGIN AUTOMÁTICO
    # -----------------------------------------
    page.goto("https://www.linkedin.com/login")

    page.fill('input[name="session_key"]', email)
    page.fill('input[name="session_password"]', password)

    try:
        page.click('button[type="submit"]')
    except:
        pass

    # Esperar redirecionamento OU captcha
    try:
        page.wait_for_url(re.compile(r"linkedin\.com/(feed|checkpoint)/"), timeout=20000)
    except:
        pass

    # -----------------------------------------
    # CAPTCHA LOCAL (mesma aba)
    # -----------------------------------------
    api_key = os.environ.get("ANTI_CAPTCHA_KEY")

    if api_key and _recaptcha_present(page):
        print("[AUTH] Recaptcha detectado — iniciando 2Captcha")
        token = _solve_recaptcha(page, api_key)
        if token:
            try:
                f = _get_captcha_frame(page)
                if f:
                    _try_submit_captcha_frame(f)
            except:
                pass

        # reenviar submit
        try:
            page.click('button[type="submit"]')
        except:
            pass

        try:
            page.wait_for_url(re.compile(r"linkedin\.com/(feed|checkpoint)/"), timeout=120000)
        except:
            pass

    # salvar estado
    try:
        context.storage_state(path=storage_path)
    except:
        pass

    return browser, context


# ================================================================
# DETECÇÃO DE CAPTCHA
# ================================================================
def _recaptcha_present(page: Page) -> bool:
    try:
        if page.locator('iframe[src*="recaptcha"]').count() > 0:
            return True
    except:
        pass
    try:
        if page.locator('.g-recaptcha').count() > 0:
            return True
    except:
        pass
    try:
        if page.locator('.grecaptcha-badge').count() > 0:
            return True
    except:
        pass
    try:
        if _get_captcha_frame(page):
            return True
    except:
        pass
    return False


def _get_captcha_frame(page: Page) -> Frame | None:
    try:
        for f in page.frames:
            if "captcha" in (f.url or "") or "/checkpoint/challenge/" in f.url:
                return f
    except:
        pass
    return None


# ================================================================
# EXTRAÇÃO DO SITEKEY
# ================================================================
def _extract_recaptcha_sitekey(page: Page) -> str:
    f = _get_captcha_frame(page)

    targets = [
        ('iframe[src*="recaptcha"]', 'src'),
        ('.g-recaptcha', 'data-sitekey'),
    ]

    check = [page]
    if f:
        check.append(f)

    for scope in check:
        for selector, attr in targets:
            try:
                el = scope.locator(selector)
                if el.count() > 0:
                    val = el.first.get_attribute(attr)
                    if val:
                        if attr == "src":
                            q = parse_qs(urlparse(val).query)
                            for k in ("k", "render", "sitekey"):
                                if k in q:
                                    return q[k][0]
                        else:
                            return val
            except:
                pass

    return ""


# ================================================================
# 2CAPTCHA (substitui anti-captcha)
# ================================================================
def _solve_recaptcha(page: Page, api_key: str) -> str:
    """
    Detecta automaticamente tipo de recaptcha (normal, invisible, enterprise)
    e cria task no 2captcha; faz polling e injeta o token quando obtido.
    """
    sitekey = _extract_recaptcha_sitekey(page)
    if not sitekey:
        print("[2CAPTCHA] Nenhum sitekey encontrado.")
        return ""

    info = _get_recaptcha_task_info(page)
    website_url = info.get("website_url") or page.url
    enterprise = info.get("enterprise") or False
    invisible = info.get("invisible") or False

    print(f"[2CAPTCHA] sitekey={sitekey} enterprise={enterprise} invisible={invisible} url={website_url}")

    # Monta a URL de criação de task (in.php)
    params = [
        ("key", api_key),
        ("method", "userrecaptcha"),
        ("googlekey", sitekey),
        ("pageurl", website_url),
        ("json", "1")
    ]
    # Adiciona flags
    if enterprise:
        params.append(("enterprise", "1"))
    if invisible:
        params.append(("invisible", "1"))

    create_url = "https://2captcha.com/in.php?" + "&".join([f"{k}={v}" for k, v in params])

    try:
        req = Request(create_url)
        res = urlopen(req, timeout=30)
        data = json.loads(res.read().decode())
        print("[2CAPTCHA] create response:", data)
    except Exception as e:
        print("[2CAPTCHA] erro create task:", e)
        return ""

    if data.get("status") != 1:
        print("[2CAPTCHA] create task falhou:", data)
        return ""

    task_id = data.get("request")
    if not task_id:
        print("[2CAPTCHA] task_id não retornado")
        return ""

    # Polling pelo resultado
    deadline = time.time() + 150  # 150s de timeout
    while time.time() < deadline:
        try:
            fetch_url = f"https://2captcha.com/res.php?key={api_key}&action=get&id={task_id}&json=1"
            req2 = Request(fetch_url)
            res2 = urlopen(req2, timeout=15)
            data2 = json.loads(res2.read().decode())
            # exemplo: {"status":1,"request":"TOKEN"}
            print("[2CAPTCHA] poll:", data2)
            if data2.get("status") == 1:
                token = data2.get("request")
                if token:
                    print("[2CAPTCHA] token obtido")
                    _inject_recaptcha_token(page, token)
                    return token
            # status 0 -> request contains message, ex: ERROR_CAPTCHA_UNSOLVABLE or CAPCHA_NOT_READY
            time.sleep(2)
        except Exception as e:
            print("[2CAPTCHA] polling error:", e)
            time.sleep(3)

    print("[2CAPTCHA] timeout aguardando token")
    return ""


def _inject_recaptcha_token(page: Page, token: str):
    """
    Injeta token no DOM pai e na frame do captcha quando possível.
    Mantém comportamento simples compatível com o restante do seu código.
    """
    print("[2CAPTCHA] injetando token na página")

    script = """
        (t) => {
            var ids = [
                'g-recaptcha-response',
                'g-recaptcha-response-100000',
                'recaptcha-token',
                'h-captcha-response'
            ];
            for (var i=0;i<ids.length;i++){
                var id = ids[i];
                var el = document.getElementById(id) || document.querySelector('textarea[name="'+id+'"]') || document.querySelector('#'+id);
                if (!el){
                    el = document.createElement('textarea');
                    el.id = id;
                    el.name = id;
                    el.style.display = 'none';
                    document.body.appendChild(el);
                }
                el.value = t;
                el.dispatchEvent(new Event('input',{bubbles:true}));
                el.dispatchEvent(new Event('change',{bubbles:true}));
            }
        }
    """
    try:
        page.evaluate(script, token)
    except Exception:
        pass

    # injeta dentro do frame se existir
    try:
        f = _get_captcha_frame(page)
        if f:
            try:
                f.evaluate(script, token)
            except Exception:
                pass
    except Exception:
        pass

    # tenta disparar callback conhecido (melhora aceitação em alguns sites)
    try:
        callback_js = """
            (t) => {
                try {
                    const cfg = window.___grecaptcha_cfg || window.___grecaptcha_clients;
                    if (cfg) {
                        var clients = (cfg.clients || cfg);
                        for (var c in clients) {
                            try {
                                var client = clients[c];
                                for (var k in client) {
                                    try {
                                        var obj = client[k];
                                        if (obj && typeof obj.callback === 'function'){
                                            try { obj.callback(t); } catch(e){}
                                        }
                                        // tentar localizar métodos com nomes diferentes
                                        if (obj && obj.execute && typeof obj.execute === 'function') {
                                            try { obj.execute(t); } catch(e){}
                                        }
                                    } catch(e){}
                                }
                            } catch(e){}
                        }
                    }
                } catch(e){}
            }
        """
        page.evaluate(callback_js, token)
    except Exception:
        pass

    # Após injeção do token, tenta submeter o checkpoint
    try:
        _submit_checkpoint(page)
    except:
        pass


# ================================================================
# SUBMIT / CHECKPOINT
# ================================================================
def _try_submit_captcha_frame(f: Frame):
    try:
        btn = f.get_by_role("button", name=re.compile(r"(Continuar|Enviar|Verificar|Avançar)", re.I))
        if btn.count() > 0:
            btn.first.click()
    except:
        pass


def _submit_checkpoint(page: Page):
    buttons = [
        ('button[type="submit"]', None),
        (None, r"(Continuar|Enviar|Verificar|Avançar|Continue|Submit)")
    ]

    for sel, regex in buttons:
        try:
            if sel:
                btn = page.locator(sel)
            else:
                btn = page.get_by_role("button", name=re.compile(regex, re.I))

            if btn.count() > 0:
                try:
                    btn.first.click()
                except:
                    try:
                        btn.first.click(force=True)
                    except:
                        pass

                try:
                    page.wait_for_url(re.compile(r"linkedin\.com/(feed|checkpoint)/"), timeout=30000)
                except:
                    pass
                return
        except:
            pass


# ================================================================
# CAPTCHA METADATA
# ================================================================
def _get_recaptcha_task_info(page: Page) -> dict:
    info = {
        "website_url": page.url,
        "enterprise": False,
        "api_domain": "",
        "invisible": False
    }

    try:
        frame = _get_captcha_frame(page)
        check = [frame] if frame else []
        check.append(page)

        for scope in check:
            fr = scope.locator('iframe[src*="recaptcha"]')
            if fr.count() > 0:
                src = fr.first.get_attribute("src") or ""
                host = urlparse(src).netloc

                if "recaptcha.net" in host:
                    info["api_domain"] = "recaptcha.net"
                elif "google.com" in host:
                    info["api_domain"] = "google.com"

                q = parse_qs(urlparse(src).query)
                if q.get("size", [""])[0] == "invisible":
                    info["invisible"] = True

            if scope.locator('.grecaptcha-badge').count() > 0:
                info["invisible"] = True

            if scope.locator('script[src*="recaptcha/enterprise.js"]').count() > 0:
                info["enterprise"] = True

    except:
        pass

    return info


# ================================================================
# NAVEGAÇÃO E POPUP GUARD
# ================================================================
def _setup_navigation_guards(context: BrowserContext, main_page: Page):
    def on_page(p: Page):
        try:
            url = p.url

            # Se for ABA 2 → fechar imediatamente e redirecionar
            if p != main_page and "linkedin.com/uas/login" in url:

                query = re.search(r"\?(.*)", url)
                if query:
                    params = parse_qs(query.group(1))
                    red = (params.get("session_redirect") or [None])[0]
                    if red:
                        try:
                            main_page.goto(unquote(red))
                        except:
                            pass

                try:
                    p.close()
                except:
                    pass

        except:
            pass

    context.on("page", on_page)
