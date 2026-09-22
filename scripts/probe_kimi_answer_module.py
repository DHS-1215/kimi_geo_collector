from playwright.sync_api import (
    sync_playwright,
)

from app.kimi.answer import (
    wait_for_answer,
)

CDP_URL = "http://127.0.0.1:9224"

INPUT_SELECTOR = (
    '.chat-input-editor'
    '[contenteditable="true"]'
    '[data-lexical-editor="true"]'
    '[role="textbox"]'
)

SEND_SELECTOR = ".send-button-container"

ASSISTANT_ITEM_SELECTOR = (
    ".chat-content-item-assistant"
)


def main():
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

        old_count = page.locator(
            ASSISTANT_ITEM_SELECTOR
        ).count()

        question = (
            "请用三句话说明"
            "Python 是什么。"
        )

        input_box = page.locator(
            INPUT_SELECTOR
        )

        input_box.click()
        input_box.fill(question)

        page.locator(
            SEND_SELECTOR
        ).click()

        print(
            "发送前 assistant:",
            old_count
        )

        print(
            "已发送:",
            question
        )

        answer = wait_for_answer(
            page,
            old_count,
            timeout=120,
            poll_interval=0.5,
            stable_seconds=2.0,
        )

        print(
            "\n===== KIMI ANSWER ====="
        )

        print(answer)


if __name__ == "__main__":
    main()
