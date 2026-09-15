import json

from playwright.sync_api import sync_playwright

from app.kimi.client import KimiClient
from app.kimi.selectors import (
    ASSISTANT_ITEM_SELECTOR,
)


CDP_URL = "http://127.0.0.1:9222"


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
            answer_timeout_seconds=180,
        )

        question = (
            "请检索公开网页，"
            "介绍鸿茅药酒的基本信息，"
            "并说明你的信息来源。"
        )

        print("开始提问：", question)

        answer = client.ask(question)

        print("\n===== ANSWER =====")
        print(answer)

        assistants = page.locator(
            ASSISTANT_ITEM_SELECTOR
        )

        latest = assistants.last

        data = latest.evaluate(
            """
            root => {
                const anchors = [
                    ...root.querySelectorAll('a')
                ].map((el, index) => ({
                    index,
                    text: (
                        el.innerText ||
                        el.textContent ||
                        ''
                    ).trim(),
                    href:
                        el.getAttribute('href') || '',
                    target:
                        el.getAttribute('target') || '',
                    class:
                        typeof el.className === 'string'
                            ? el.className
                            : '',
                    html:
                        el.outerHTML.slice(0, 1000)
                }));

                const all = [
                    ...root.querySelectorAll('*')
                ];

                const candidates = all
                    .filter(el => {
                        const cls = (
                            typeof el.className
                                === 'string'
                                ? el.className
                                : ''
                        ).toLowerCase();

                        const text = (
                            el.innerText ||
                            el.textContent ||
                            ''
                        ).trim().toLowerCase();

                        const aria = (
                            el.getAttribute(
                                'aria-label'
                            ) || ''
                        ).toLowerCase();

                        const value =
                            cls + ' ' +
                            text + ' ' +
                            aria;

                        return (
                            value.includes('source') ||
                            value.includes('reference') ||
                            value.includes('citation') ||
                            value.includes('search') ||
                            value.includes('link') ||
                            value.includes('引用') ||
                            value.includes('来源') ||
                            value.includes('搜索')
                        );
                    })
                    .map((el, index) => ({
                        index,
                        tag: el.tagName,
                        class:
                            typeof el.className === 'string'
                                ? el.className
                                : '',
                        ariaLabel:
                            el.getAttribute(
                                'aria-label'
                            ) || '',
                        text: (
                            el.innerText ||
                            el.textContent ||
                            ''
                        ).trim().slice(0, 500),
                        html:
                            el.outerHTML.slice(0, 1200)
                    }));

                return {
                    anchors,
                    candidates
                };
            }
            """
        )

        print(
            "\n===== ASSISTANT SOURCE DOM ====="
        )

        print(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()