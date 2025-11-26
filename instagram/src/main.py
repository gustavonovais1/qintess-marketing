import argparse
import json
import os
from playwright.sync_api import sync_playwright
from .auth import create_context

def main():
    parser = argparse.ArgumentParser()
    # Salva o storage_state dentro da pasta instagram por padrão
    parser.add_argument("--storage", default="instagram/instagram_storage.json")
    parser.add_argument("--stay-open", action="store_true")
    args = parser.parse_args()
    with sync_playwright() as p:
        browser = None
        context = None
        try:
            browser, context = create_context(p, args.storage)
            page = context.new_page()
            page.goto("https://www.instagram.com/")
            print(json.dumps({"navigated_to": page.url}, ensure_ascii=False))
            headless_env = os.environ.get("HEADLESS", "true").lower()
            stay_open = args.stay_open or headless_env in ("false", "0", "no")
            if stay_open:
                page.wait_for_timeout(24 * 60 * 60 * 1000)
        finally:
            if context:
                context.close()
            if browser:
                browser.close()

if __name__ == "__main__":
    main()