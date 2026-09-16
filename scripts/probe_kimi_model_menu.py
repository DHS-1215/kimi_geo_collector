import json
import time

from playwright.sync_api import sync_playwright

CDP_URL = "http://127.0.0.1:9222"

MODEL_SWITCH_SELECTOR = ".current-model"


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

        trigger = page.locator(
            MODEL_SWITCH_SELECTOR
        ).first

        print("模型入口数量:", trigger.count())

        if trigger.count() != 1:
            raise RuntimeError(
                f"模型入口数量异常: {trigger.count()}"
            )

        print("\n===== 当前状态 =====")

        print(
            "入口文本:",
            repr(
                trigger.inner_text().strip()
            )
        )

        print(
            "aria-expanded:",
            trigger.get_attribute(
                "aria-expanded"
            )
        )

        menu_id = trigger.get_attribute(
            "aria-controls"
        )

        print(
            "aria-controls:",
            menu_id
        )

        trigger.click()

        time.sleep(0.5)

        print("\n===== 点击后 =====")

        print(
            "aria-expanded:",
            trigger.get_attribute(
                "aria-expanded"
            )
        )

        if menu_id:
            menu = page.locator(
                f"#{menu_id}"
            )
        else:
            menu = page.locator(
                '[role="menu"]:visible'
            ).last

        print(
            "菜单数量:",
            menu.count()
        )

        if menu.count() == 0:
            raise RuntimeError(
                "点击模型入口后没有找到菜单"
            )

        menu = menu.first

        data = menu.evaluate(
            """
            root => {
                const selectors = [
                    'button',
                    '[role="menuitem"]',
                    '[role="menuitemradio"]',
                    '[role="option"]',
                    '[role="radio"]',
                    '[aria-checked]',
                    '[aria-selected]'
                ];

                const nodes = [
                    ...new Set(
                        selectors.flatMap(
                            selector =>
                                [
                                    ...root.querySelectorAll(
                                        selector
                                    )
                                ]
                        )
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
                            20000
                        ),

                    items:
                        nodes.map(
                            (el, index) => ({
                                index,

                                tag:
                                    el.tagName,

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

                                ariaLabel:
                                    el.getAttribute(
                                        'aria-label'
                                    ) || '',

                                ariaChecked:
                                    el.getAttribute(
                                        'aria-checked'
                                    ) || '',

                                ariaSelected:
                                    el.getAttribute(
                                        'aria-selected'
                                    ) || '',

                                dataValue:
                                    el.getAttribute(
                                        'data-value'
                                    ) || '',

                                dataModel:
                                    el.getAttribute(
                                        'data-model'
                                    ) || '',

                                html:
                                    el.outerHTML.slice(
                                        0,
                                        1200
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

        # 只侦察，不选择任何菜单项
        page.keyboard.press(
            "Escape"
        )

        time.sleep(0.2)

        print(
            "\n菜单已关闭，没有修改当前模式。"
        )


if __name__ == "__main__":
    main()
