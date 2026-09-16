import json
import time

from playwright.sync_api import sync_playwright

CDP_URL = "http://127.0.0.1:9222"

MODEL_SWITCH_SELECTOR = ".current-model"

EFFORT_ITEM_SELECTOR = "button.effort-item"


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

        model_trigger = page.locator(
            MODEL_SWITCH_SELECTOR
        ).first

        model_trigger.click()

        time.sleep(0.3)

        effort_item = page.locator(
            EFFORT_ITEM_SELECTOR
        ).first

        print(
            "思考强度入口数量:",
            effort_item.count(),
        )

        if effort_item.count() != 1:
            raise RuntimeError(
                "没有找到唯一的思考强度入口"
            )

        print(
            "当前入口文本:",
            repr(
                effort_item.inner_text().strip()
            ),
        )

        submenu_id = effort_item.get_attribute(
            "aria-controls"
        )

        print(
            "aria-controls:",
            submenu_id,
        )

        effort_item.click()

        time.sleep(0.3)

        if submenu_id:
            menu = page.locator(
                f"#{submenu_id}"
            )
        else:
            menu = page.locator(
                '[role="menu"]:visible'
            ).last

        print(
            "子菜单数量:",
            menu.count(),
        )

        if menu.count() == 0:
            raise RuntimeError(
                "未找到思考强度子菜单"
            )

        menu = menu.first

        data = menu.evaluate(
            """
            root => {
                const items = [
                    ...root.querySelectorAll(
                        [
                            'button',
                            '[role="menuitemradio"]',
                            '[role="menuitem"]',
                            '[aria-checked]'
                        ].join(',')
                    )
                ];

                return {
                    text: (
                        root.innerText ||
                        root.textContent ||
                        ''
                    ).trim(),

                    html:
                        root.outerHTML.slice(
                            0,
                            15000
                        ),

                    items:
                        items.map(
                            (el, index) => ({
                                index,

                                text:
                                    (
                                        el.innerText ||
                                        el.textContent ||
                                        ''
                                    )
                                    .trim()
                                    .slice(
                                        0,
                                        300
                                    ),

                                class:
                                    typeof el.className
                                        === 'string'
                                        ? el.className
                                        : '',

                                role:
                                    el.getAttribute(
                                        'role'
                                    ) || '',

                                ariaChecked:
                                    el.getAttribute(
                                        'aria-checked'
                                    ) || '',

                                ariaSelected:
                                    el.getAttribute(
                                        'aria-selected'
                                    ) || '',

                                html:
                                    el.outerHTML.slice(
                                        0,
                                        1000
                                    )
                            })
                        )
                };
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

        page.keyboard.press(
            "Escape"
        )

        time.sleep(0.2)

        page.keyboard.press(
            "Escape"
        )

        print(
            "\n已关闭菜单，没有修改任何设置。"
        )


if __name__ == "__main__":
    main()
