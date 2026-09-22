import json
import time

from playwright.sync_api import sync_playwright

CDP_URL = "http://127.0.0.1:9224"

MODEL_SWITCH_SELECTOR = ".current-model"

MODEL_NAMES = (
    "快速",
    "K3",
    "K3 集群",
)


def get_current_profile(page):
    trigger = page.locator(
        MODEL_SWITCH_SELECTOR
    ).first

    model = (
        trigger.locator(
            ".model-name .name"
        ).inner_text().strip()
    )

    effort_node = trigger.locator(
        ".current-effort"
    )

    effort = (
        effort_node.inner_text().strip()
        if effort_node.count()
        else ""
    )

    return {
        "model": model,
        "effort": effort,
        "text": trigger.inner_text().strip(),
    }


def open_model_menu(page):
    trigger = page.locator(
        MODEL_SWITCH_SELECTOR
    ).first

    if (
            trigger.get_attribute(
                "aria-expanded"
            )
            != "true"
    ):
        trigger.click()
        time.sleep(0.3)

    return trigger


def select_model(
        page,
        model_name: str,
):
    open_model_menu(page)

    options = page.locator(
        'button.model-item'
        '[role="menuitemradio"]'
    )

    target = None

    for index in range(
            options.count()
    ):
        option = options.nth(index)

        name_node = option.locator(
            ".model-name .name"
        )

        if not name_node.count():
            continue

        name = (
            name_node
            .inner_text()
            .strip()
        )

        if name == model_name:
            target = option
            break

    if target is None:
        raise RuntimeError(
            f"没有找到模型: {model_name}"
        )

    if (
            target.get_attribute(
                "aria-checked"
            )
            != "true"
    ):
        target.click()
        time.sleep(1.0)


def inspect_efforts(page):
    open_model_menu(page)

    effort_entry = page.locator(
        "button.effort-item"
    ).first

    if (
            effort_entry.count() == 0
            or not effort_entry.is_visible()
    ):
        page.keyboard.press(
            "Escape"
        )

        return {
            "available": False,
            "current": "",
            "options": [],
        }

    current_node = effort_entry.locator(
        ".effort-value"
    )

    current = (
        current_node.inner_text().strip()
        if current_node.count()
        else ""
    )

    submenu_id = (
        effort_entry.get_attribute(
            "aria-controls"
        )
    )

    effort_entry.click()
    time.sleep(0.3)

    if submenu_id:
        submenu = page.locator(
            f"#{submenu_id}"
        )
    else:
        submenu = page.locator(
            '[role="menu"]:visible'
        ).last

    options = []

    if submenu.count():
        items = submenu.locator(
            'button.effort-option'
            '[role="menuitemradio"]'
        )

        for index in range(
                items.count()
        ):
            item = items.nth(index)

            options.append(
                {
                    "text":
                        item.inner_text().strip(),

                    "checked":
                        item.get_attribute(
                            "aria-checked"
                        ),
                }
            )

    page.keyboard.press(
        "Escape"
    )

    time.sleep(0.1)

    page.keyboard.press(
        "Escape"
    )

    return {
        "available": True,
        "current": current,
        "options": options,
    }


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

        original = get_current_profile(
            page
        )

        print(
            "原始状态:",
            original,
        )

        results = []

        try:
            for model_name in MODEL_NAMES:
                print()
                print(
                    "=" * 60
                )

                print(
                    "切换模型:",
                    model_name
                )

                select_model(
                    page,
                    model_name,
                )

                profile = (
                    get_current_profile(
                        page
                    )
                )

                effort_info = (
                    inspect_efforts(
                        page
                    )
                )

                result = {
                    "requested_model":
                        model_name,

                    "current_profile":
                        profile,

                    "effort":
                        effort_info,

                    "url":
                        page.url,
                }

                results.append(
                    result
                )

                print(
                    json.dumps(
                        result,
                        ensure_ascii=False,
                        indent=2,
                    )
                )

        finally:
            print()
            print(
                "=" * 60
            )

            print(
                "恢复原模型:",
                original["model"]
            )

            select_model(
                page,
                original["model"],
            )

            # 暂时只恢复模型。
            # effort 不做修改，
            # 因为探针全程没有点击具体 effort。

            print(
                "恢复后:",
                get_current_profile(
                    page
                )
            )

        print(
            "\n===== MATRIX ====="
        )

        print(
            json.dumps(
                results,
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
