import json

from playwright.sync_api import sync_playwright

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

        print("URL:", page.url)

        result = page.evaluate(
            """
            () => {
                const nodes = [
                    ...document.querySelectorAll(
                        'button, a, div, span'
                    )
                ];

                function isVisible(el) {
                    const style =
                        getComputedStyle(el);

                    const rect =
                        el.getBoundingClientRect();

                    return (
                        style.display !== 'none' &&
                        style.visibility !== 'hidden' &&
                        rect.width > 0 &&
                        rect.height > 0
                    );
                }

                return nodes
                    .filter(isVisible)
                    .filter(el => {
                        const text = (
                            el.innerText ||
                            el.textContent ||
                            ''
                        ).trim();

                        const aria = (
                            el.getAttribute(
                                'aria-label'
                            ) || ''
                        ).trim();

                        const title = (
                            el.getAttribute(
                                'title'
                            ) || ''
                        ).trim();

                        const value =
                            text + ' ' +
                            aria + ' ' +
                            title;

                        return (
                            value.includes('新建会话') ||
                            value.includes('新对话') ||
                            value.includes('新建对话')
                        );
                    })
                    .map((el, index) => ({
                        index,
                        tag: el.tagName,
                        text: (
                            el.innerText ||
                            el.textContent ||
                            ''
                        ).trim().slice(0, 200),
                        class:
                            typeof el.className
                            === 'string'
                                ? el.className
                                : '',
                        id: el.id || '',
                        role:
                            el.getAttribute('role') || '',
                        ariaLabel:
                            el.getAttribute(
                                'aria-label'
                            ) || '',
                        href:
                            el.getAttribute('href') || '',
                        title:
                            el.getAttribute('title') || '',
                        html:
                            el.outerHTML.slice(
                                0,
                                2500
                            )
                    }));
            }
            """
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
