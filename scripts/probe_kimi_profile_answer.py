from playwright.sync_api import (
    sync_playwright,
)

from app.kimi.client import (
    KimiClient,
)

from app.kimi.types import (
    KimiMode,
    KimiModel,
)

CDP_URL = "http://127.0.0.1:9222"

CASES = (
    (
        KimiModel.FAST,
        KimiMode.ADVANCED,
    ),
    (
        KimiModel.K3,
        KimiMode.EXTREME,
    ),
    (
        KimiModel.K3_CLUSTER,
        KimiMode.EXTREME,
    ),
)


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
            answer_timeout_seconds=240,
        )

        success = 0

        for model, mode in CASES:
            print()
            print(
                "=" * 70
            )

            print(
                "PROFILE:",
                model.value,
                "+",
                mode.value,
            )

            try:
                client.set_profile(
                    model=model,
                    mode=mode,
                )

                print(
                    "URL BEFORE:",
                    page.url,
                )

                question = (
                    "请用一句话说明什么是人工智能。"
                )

                before_answer_count = (
                    client._answer_count()
                )

                client._fill_question(
                    question
                )

                client._send()

                page.wait_for_timeout(
                    1000
                )

                blocking = detect_blocking_dialog(
                    page
                )

                if blocking:
                    print(
                        "BLOCKED:",
                        blocking,
                    )

                    close_blocking_dialog(
                        page
                    )

                    print(
                        "RESULT: BLOCKED"
                    )

                    continue

                answer = (
                    client._wait_for_new_answer_complete(
                        before_answer_count
                    )
                )

                print(
                    "URL AFTER:",
                    page.url,
                )

                print(
                    "ANSWER:",
                    answer,
                )

                passed = bool(
                    answer.strip()
                )

                print(
                    "RESULT:",
                    "PASS"
                    if passed
                    else "FAIL",
                )

                if passed:
                    success += 1

            except Exception as e:
                print(
                    "RESULT: FAIL"
                )

                print(
                    "ERROR:",
                    repr(e),
                )

        print()
        print(
            "=" * 70
        )

        print(
            f"PASS: {success}/{len(CASES)}"
        )

def detect_blocking_dialog(
        page,
) -> str | None:

    markers = (
        "和Kimi聊天的人太多了",
        "订阅会员可进入优先队列",
    )

    for marker in markers:
        node = page.get_by_text(
            marker,
            exact=False,
        )

        if (
            node.count() > 0
            and node.first.is_visible()
        ):
            return marker

    return None


def close_blocking_dialog(
        page,
) -> None:

    button = page.get_by_role(
        "button",
        name="我知道了",
    )

    if (
        button.count() > 0
        and button.first.is_visible()
    ):
        button.first.click()

        page.wait_for_timeout(
            300
        )


if __name__ == "__main__":
    main()
