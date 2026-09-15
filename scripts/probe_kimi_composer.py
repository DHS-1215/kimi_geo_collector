import json
import time

from playwright.sync_api import sync_playwright


CDP_URL = "http://127.0.0.1:9222"

INPUT_SELECTOR = (
    '.chat-input-editor'
    '[contenteditable="true"]'
    '[data-lexical-editor="true"]'
    '[role="textbox"]'
)


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

        input_box = page.locator(INPUT_SELECTOR)

        print("输入框数量:", input_box.count())

        if input_box.count() != 1:
            raise RuntimeError(
                f"KIMI 输入框数量异常: {input_box.count()}"
            )

        # 只输入测试文字，不发送
        input_box.click()
        input_box.fill("GEO_PROBE_ONLY")

        time.sleep(1)

        result = page.evaluate(
            """
            () => {
                const input = document.querySelector(
                    '.chat-input-editor[data-lexical-editor="true"]'
                );

                if (!input) {
                    return {
                        error: 'input not found'
                    };
                }

                // 向上寻找输入区域容器
                let root = input;

                for (let i = 0; i < 5 && root.parentElement; i++) {
                    root = root.parentElement;
                }

                const elements = [
                    ...root.querySelectorAll(
                        'button, [role="button"], [aria-label]'
                    )
                ];

                return {
                    inputHTML: input.outerHTML,

                    containerHTML:
                        root.outerHTML.slice(0, 12000),

                    controls: elements.map((el, index) => ({
                        index,
                        tag: el.tagName,
                        id: el.id || '',
                        class:
                            typeof el.className === 'string'
                                ? el.className
                                : '',
                        role:
                            el.getAttribute('role') || '',
                        ariaLabel:
                            el.getAttribute('aria-label') || '',
                        title:
                            el.getAttribute('title') || '',
                        disabled:
                            el.disabled ?? false,
                        ariaDisabled:
                            el.getAttribute('aria-disabled') || '',
                        text: (
                            el.innerText ||
                            el.textContent ||
                            ''
                        ).trim().slice(0, 120),
                        html:
                            el.outerHTML.slice(0, 800)
                    }))
                };
            }
            """
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

        # 清理测试文字
        input_box.fill("")

        print("\n测试文字已清空，没有发送。")


if __name__ == "__main__":
    main()