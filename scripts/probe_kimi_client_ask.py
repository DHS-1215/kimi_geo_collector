from playwright.sync_api import (
    sync_playwright,
)

from app.kimi.client import KimiClient


CDP_URL = "http://127.0.0.1:9224"


def main() -> None:
    with sync_playwright() as p:
        browser = (
            p.chromium.connect_over_cdp(
                CDP_URL
            )
        )

        pages = [
            page
            for context in browser.contexts
            for page in context.pages
        ]

        page = next(
            page
            for page in pages
            if "kimi.com"
            in page.url.lower()
        )

        client = KimiClient(
            page=page,
            answer_timeout_seconds=120,
        )

        answer = client.ask(
            "请用三句话介绍 FastAPI。"
        )

        print(
            "\n===== KIMI CLIENT ANSWER ====="
        )

        print(answer)


if __name__ == "__main__":
    main()