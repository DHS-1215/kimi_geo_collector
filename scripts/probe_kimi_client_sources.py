from playwright.sync_api import sync_playwright

from app.kimi.client import KimiClient

CDP_URL = "http://127.0.0.1:9222"


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
            answer_timeout_seconds=180,
        )

        question = (
            "请检索公开网页，"
            "介绍鸿茅药酒的基本信息，"
            "并说明你的信息来源。"
        )

        answer = client.ask(
            question
        )

        sources = client.get_sources()

        print(
            "\n===== ANSWER ====="
        )
        print(answer)

        print(
            "\n===== SOURCES ====="
        )
        print(
            "SOURCE COUNT:",
            len(sources)
        )

        for source in sources:
            print()
            print(
                f"[{source.index}] "
                f"{source.source}"
            )
            print(
                "URL:",
                source.url
            )
            print(
                "DOMAIN:",
                source.domain
            )


if __name__ == "__main__":
    main()
