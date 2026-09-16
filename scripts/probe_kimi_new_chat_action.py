from playwright.sync_api import sync_playwright

from app.kimi.client import KimiClient
from app.kimi.selectors import (
    ASSISTANT_ITEM_SELECTOR,
    QUESTION_ITEM_SELECTOR,
)

CDP_URL = "http://127.0.0.1:9223"


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
            page=page
        )

        print("BEFORE URL:", page.url)

        print(
            "BEFORE QUESTION COUNT:",
            page.locator(
                QUESTION_ITEM_SELECTOR
            ).count(),
        )

        print(
            "BEFORE ANSWER COUNT:",
            page.locator(
                ASSISTANT_ITEM_SELECTOR
            ).count(),
        )

        client.new_chat()

        print("AFTER URL:", page.url)

        print(
            "AFTER QUESTION COUNT:",
            page.locator(
                QUESTION_ITEM_SELECTOR
            ).count(),
        )

        print(
            "AFTER ANSWER COUNT:",
            page.locator(
                ASSISTANT_ITEM_SELECTOR
            ).count(),
        )

        print("RESULT: PASS")


if __name__ == "__main__":
    main()
