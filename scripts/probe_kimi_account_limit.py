import time

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
            if "kimi.com"
            in page.url.lower()
        )

        client = KimiClient(
            page=page,
            answer_timeout_seconds=240,
        )

        client.set_profile(
            model=KimiModel.K3,
            mode=KimiMode.EXTREME,
        )

        print(
            "PROFILE:",
            client._current_model(),
            "+",
            client._current_mode(),
        )

        started = time.monotonic()

        try:
            answer = client.ask(
                "请用一句话说明什么是人工智能。"
            )

            elapsed = (
                    time.monotonic()
                    - started
            )

            print(
                "UNEXPECTED ANSWER:",
                answer,
            )

            print(
                f"ELAPSED: {elapsed:.2f}s"
            )

        except Exception as e:
            elapsed = (
                    time.monotonic()
                    - started
            )

            print(
                "ERROR:",
                repr(e),
            )

            print(
                f"ELAPSED: {elapsed:.2f}s"
            )

            text = str(e)

            passed = (
                    "KIMI_ACCOUNT_SWITCH_REQUIRED"
                    in text
                    and elapsed < 5
            )

            print(
                "RESULT:",
                "PASS"
                if passed
                else "FAIL",
            )


if __name__ == "__main__":
    main()
