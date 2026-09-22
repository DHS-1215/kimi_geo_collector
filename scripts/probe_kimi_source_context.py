import json

from playwright.sync_api import sync_playwright

from app.kimi.selectors import (
    ASSISTANT_ITEM_SELECTOR,
)

CDP_URL = "http://127.0.0.1:9224"


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
            if "kimi.com" in page.url.lower()
        )

        assistants = page.locator(
            ASSISTANT_ITEM_SELECTOR
        )

        latest = assistants.last

        data = latest.evaluate(
            """
            root => {
                const anchors = [
                    ...root.querySelectorAll(
                        'a.pua-ref-cite-tag[href]'
                    )
                ];

                return anchors.map(
                    (anchor, index) => {
                        const parent =
                            anchor.parentElement;

                        const grand =
                            parent
                                ? parent.parentElement
                                : null;

                        const great =
                            grand
                                ? grand.parentElement
                                : null;

                        return {
                            index,

                            href:
                                anchor.href || '',

                            rawHref:
                                anchor.getAttribute(
                                    'href'
                                ) || '',

                            siteName:
                                anchor.getAttribute(
                                    'data-site-name'
                                ) || '',

                            text:
                                (
                                    anchor.innerText ||
                                    anchor.textContent ||
                                    ''
                                ).trim(),

                            attributes:
                                [...anchor.attributes]
                                    .reduce(
                                        (obj, attr) => {
                                            obj[
                                                attr.name
                                            ] = attr.value;

                                            return obj;
                                        },
                                        {}
                                    ),

                            parentText:
                                parent
                                    ? (
                                        parent.innerText ||
                                        parent.textContent ||
                                        ''
                                      )
                                        .trim()
                                        .slice(0, 800)
                                    : '',

                            parentHTML:
                                parent
                                    ? parent.outerHTML
                                        .slice(0, 2000)
                                    : '',

                            grandText:
                                grand
                                    ? (
                                        grand.innerText ||
                                        grand.textContent ||
                                        ''
                                      )
                                        .trim()
                                        .slice(0, 1200)
                                    : '',

                            grandHTML:
                                grand
                                    ? grand.outerHTML
                                        .slice(0, 3000)
                                    : '',

                            greatText:
                                great
                                    ? (
                                        great.innerText ||
                                        great.textContent ||
                                        ''
                                      )
                                        .trim()
                                        .slice(0, 1500)
                                    : ''
                        };
                    }
                );
            }
            """
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
