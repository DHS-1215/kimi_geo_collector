import time

from playwright.sync_api import sync_playwright

CDP_URL = "http://127.0.0.1:9224"

INPUT_SELECTOR = (
    '.chat-input-editor'
    '[contenteditable="true"]'
    '[data-lexical-editor="true"]'
    '[role="textbox"]'
)

SEND_SELECTOR = ".send-button-container"


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)

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

        print("发送前 URL:", page.url)

        input_box = page.locator(INPUT_SELECTOR)
        send_button = page.locator(SEND_SELECTOR)

        print("输入框数量:", input_box.count())
        print("发送按钮数量:", send_button.count())

        if input_box.count() != 1:
            raise RuntimeError(
                f"输入框数量异常: {input_box.count()}"
            )

        if send_button.count() != 1:
            raise RuntimeError(
                f"发送按钮数量异常: {send_button.count()}"
            )

        question = "你好，请用一句话介绍你自己。"

        input_box.click()
        input_box.fill(question)

        time.sleep(1)

        print("\n发送按钮 HTML:")
        print(
            send_button.evaluate(
                "el => el.outerHTML"
            )
        )

        send_button.click()

        print("\n已点击发送")

        # 观察发送后的页面变化
        for second in range(1, 11):
            time.sleep(1)

            print(
                f"[{second}s]",
                "URL:",
                page.url,
                "输入内容:",
                repr(input_box.inner_text()),
            )


if __name__ == "__main__":
    main()
