import argparse
import os
from playwright.sync_api import sync_playwright

from instagram.src.auth import create_context


def main():
    parser = argparse.ArgumentParser(
        description="Realiza login MANUAL no Instagram e salva storage_state para usos futuros."
    )
    parser.add_argument(
        "--storage",
        default=os.environ.get("IG_STORAGE_PATH", "/app/instagram/instagram_storage.json"),
        help="Caminho do arquivo de storage_state a ser criado/utilizado.",
    )
    args = parser.parse_args()

    # Força execução em modo visível por padrão (pode ser sobrescrito pelo usuário)
    os.environ.setdefault("HEADLESS", "false")

    with sync_playwright() as p:
        # create_context já faz:
        # - abrir página de login do Instagram
        # - esperar você logar manualmente (se não houver e-mail/senha em variáveis de ambiente)
        # - salvar o storage_state no caminho informado
        browser, context = create_context(p, args.storage)

        # Mantém o navegador/contexto abertos para você interagir via VNC/noVNC.
        # Você pode interromper com Ctrl+C quando não precisar mais.
        try:
            page = context.pages[0] if context.pages else context.new_page()
        except Exception:
            page = None

        if page is not None:
            # espera "infinito" (24h) até você encerrar manualmente
            page.wait_for_timeout(24 * 60 * 60 * 1000)
        else:
            # fallback: aguarda um tempo razoável
            p.sleep(300_000)


if __name__ == "__main__":
    main()


