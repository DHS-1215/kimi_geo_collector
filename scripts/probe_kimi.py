import json

from playwright.sync_api import sync_playwright

CDP_URL = "http://127.0.0.1:9222"

KIMI_HOST_HINTS = (
    "kimi.com",
    "kimi.moonshot.cn",
)


def is_kimi_page(url: str) -> bool:
    url = url.lower()
    return any(host in url for host in KIMI_HOST_HINTS)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)

        pages = [
            page
            for context in browser.contexts
            for page in context.pages
        ]

        print("\n=== 当前 CDP 页面 ===")

        for index, page in enumerate(pages):
            print(f"[{index}] {page.url}")

        kimi_page = next(
            (
                page
                for page in pages
                if is_kimi_page(page.url)
            ),
            None,
        )

        if kimi_page is None:
            raise RuntimeError(
                "没有找到 KIMI 页面，请先在当前 CDP Chrome 中打开 KIMI。"
            )

        print("\n=== 找到 KIMI 页面 ===")
        print("URL:", kimi_page.url)
        print("Title:", kimi_page.title())

        result = kimi_page.evaluate(
            """
            () => {
                const selectors = [
                    'textarea',
                    '[contenteditable="true"]',
                    'button',
                    '[role="button"]',
                    '[role="menuitem"]',
                    '[role="menuitemradio"]',
                    '[role="option"]',
                    '[role="combobox"]'
                ];

                const nodes = [
                    ...new Set(
                        selectors.flatMap(selector =>
                            [...document.querySelectorAll(selector)]
                        )
                    )
                ];

                return nodes.map((el, index) => {
                    const text = (
                        el.innerText ||
                        el.textContent ||
                        ''
                    ).trim();

                    return {
                        index,
                        tag: el.tagName,
                        id: el.id || '',
                        class:
                            typeof el.className === 'string'
                                ? el.className
                                : '',
                        role: el.getAttribute('role') || '',
                        ariaLabel:
                            el.getAttribute('aria-label') || '',
                        ariaPressed:
                            el.getAttribute('aria-pressed') || '',
                        ariaExpanded:
                            el.getAttribute('aria-expanded') || '',
                        title:
                            el.getAttribute('title') || '',
                        placeholder:
                            el.getAttribute('placeholder') ||
                            el.getAttribute('data-placeholder') ||
                            '',
                        contenteditable:
                            el.getAttribute('contenteditable') || '',
                        testid:
                            el.getAttribute('data-testid') || '',
                        text: text.slice(0, 160),
                        html: el.outerHTML.slice(0, 500),
                    };
                });
            }
            """
        )

        print("\n=== 可交互元素 ===")

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
