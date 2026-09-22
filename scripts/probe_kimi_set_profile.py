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

CASES = (
    (
        KimiModel.FAST,
        KimiMode.STANDARD,
    ),
    (
        KimiModel.FAST,
        KimiMode.ADVANCED,
    ),

    (
        KimiModel.K3,
        KimiMode.STANDARD,
    ),
    (
        KimiModel.K3,
        KimiMode.ADVANCED,
    ),
    (
        KimiModel.K3,
        KimiMode.EXTREME,
    ),

    (
        KimiModel.K3_CLUSTER,
        KimiMode.STANDARD,
    ),
    (
        KimiModel.K3_CLUSTER,
        KimiMode.ADVANCED,
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
            page=page
        )

        success = 0

        for model, mode in CASES:
            print()
            print(
                "=" * 60
            )

            print(
                "TEST:",
                model.value,
                "+",
                mode.value,
            )

            try:
                client.set_profile(
                    model=model,
                    mode=mode,
                )

                actual_model = (
                    client._current_model()
                )

                actual_mode = (
                    client._current_mode()
                )

                passed = (
                        actual_model
                        == model.value
                        and actual_mode
                        == mode.value
                )

                print(
                    "MODEL:",
                    actual_model,
                )

                print(
                    "MODE:",
                    actual_mode,
                )

                print(
                    "URL:",
                    page.url,
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
            "=" * 60
        )

        print(
            f"PASS: {success}/{len(CASES)}"
        )


if __name__ == "__main__":
    main()
