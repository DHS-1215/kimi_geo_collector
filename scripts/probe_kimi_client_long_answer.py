from playwright.sync_api import sync_playwright

from app.kimi.client import KimiClient


CDP_URL = "http://127.0.0.1:9224"


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(
            CDP_URL
        )

        pages = [
            page
            for context in browser.contexts
            for page in context.pages
        ]

        page = next(
            page
            for page in pages
            if "kimi.com" in page.url.lower()
        )

        client = KimiClient(
            page=page,
            answer_timeout_seconds=120,
        )

        question = (
            "请详细介绍人工智能的发展历程、"
            "主要技术方向、典型应用场景以及未来趋势，"
            "回答不少于800字。"
        )

        answer = client.ask(question)

        print(
            "\n===== KIMI LONG ANSWER ====="
        )

        print(answer)

        print(
            "\n===== RESULT ====="
        )

        print(
            "字符数:",
            len(answer)
        )

        print(
            "是否非空:",
            bool(answer.strip())
        )


if __name__ == "__main__":
    main()