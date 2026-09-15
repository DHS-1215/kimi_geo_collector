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

SEND_SELECTOR = ".send-button-container"


def get_kimi_page(browser):
    pages = [
        page
        for context in browser.contexts
        for page in context.pages
    ]

    return next(
        page
        for page in pages
        if "kimi.com" in page.url.lower()
    )


def inspect_page(page):
    return page.evaluate(
        """
        () => {
            function isVisible(el) {
                const style = getComputedStyle(el);
                const rect = el.getBoundingClientRect();

                return (
                    style.display !== 'none' &&
                    style.visibility !== 'hidden' &&
                    rect.width > 0 &&
                    rect.height > 0
                );
            }

            const all = [...document.querySelectorAll('*')];

            const candidates = all
                .filter(isVisible)
                .filter(el => {
                    const cls =
                        typeof el.className === 'string'
                            ? el.className.toLowerCase()
                            : '';

                    const text = (
                        el.innerText ||
                        el.textContent ||
                        ''
                    ).trim().toLowerCase();

                    const aria = (
                        el.getAttribute('aria-label') ||
                        ''
                    ).toLowerCase();

                    return (
                        cls.includes('message') ||
                        cls.includes('chat') ||
                        cls.includes('answer') ||
                        cls.includes('response') ||
                        cls.includes('markdown') ||
                        cls.includes('segment') ||
                        cls.includes('content') ||
                        cls.includes('thinking') ||
                        cls.includes('loading') ||
                        cls.includes('send') ||
                        cls.includes('stop') ||
                        text.includes('停止') ||
                        text.includes('重新生成') ||
                        aria.includes('停止')
                    );
                })
                .map(el => ({
                    tag: el.tagName,
                    id: el.id || '',
                    class:
                        typeof el.className === 'string'
                            ? el.className
                            : '',
                    role: el.getAttribute('role') || '',
                    ariaLabel:
                        el.getAttribute('aria-label') || '',
                    text: (
                        el.innerText ||
                        el.textContent ||
                        ''
                    ).trim().slice(0, 500),
                    html:
                        el.outerHTML.slice(0, 1000)
                }));

            return {
                url: location.href,

                bodyTail:
                    document.body.innerText.slice(-6000),

                candidates:
                    candidates.slice(-100)
            };
        }
        """
    )


def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)

        page = get_kimi_page(browser)

        print("起始 URL:", page.url)

        input_box = page.locator(INPUT_SELECTOR)
        send_button = page.locator(SEND_SELECTOR)

        question = (
            "什么是人工智能？"
            "请用三句话简单回答。"
        )

        input_box.click()
        input_box.fill(question)

        time.sleep(1)

        send_button.click()

        print("已发送:", question)

        last_body = ""
        stable_count = 0

        for second in range(1, 46):
            time.sleep(1)

            data = inspect_page(page)

            body = data["bodyTail"]

            if body == last_body:
                stable_count += 1
            else:
                stable_count = 0

            print(
                f"[{second:02d}s] "
                f"stable={stable_count} "
                f"url={data['url']}"
            )

            if second in (
                    1, 2, 3, 4, 5,
                    8, 12, 20, 30, 45
            ):
                print(
                    "\n===== SNAPSHOT ====="
                )

                print(
                    json.dumps(
                        data,
                        ensure_ascii=False,
                        indent=2
                    )
                )

                print(
                    "===== END =====\n"
                )

            last_body = body


if __name__ == "__main__":
    main()
