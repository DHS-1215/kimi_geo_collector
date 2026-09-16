from playwright.sync_api import sync_playwright

from app.kimi.client import KimiClient
from app.kimi.types import (
    KimiMode,
    KimiModel,
)

CDP_URL = "http://127.0.0.1:9224"


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

        client = KimiClient(
            page=page,
            answer_timeout_seconds=450,
        )

        result = client.collect(
            question=(
                "请检索公开网页，"
                "简单介绍鸿茅药酒的基本信息，"
                "并说明信息来源。"
            ),
            model=KimiModel.FAST,
            mode=KimiMode.STANDARD,
        )

        print()
        print("=" * 60)
        print("KIMI COLLECT RESULT")
        print("=" * 60)

        print(
            "STATUS:",
            result.status,
        )

        print(
            "ACQUISITION STATUS:",
            result.acquisition_status,
        )

        print(
            "MODEL:",
            result.model,
        )

        print(
            "MODE:",
            result.mode,
        )

        print(
            "COMPLETE:",
            result.is_complete,
        )

        print(
            "ANSWER LENGTH:",
            len(result.answer),
        )

        print(
            "SOURCE STATUS:",
            result.source_collection_status,
        )

        print(
            "SOURCE COUNT:",
            len(result.sources),
        )

        print(
            "URL:",
            result.conversation_url,
        )

        print(
            "ERROR:",
            result.error,
        )

        print()
        print("===== ANSWER =====")
        print(result.answer)

        print()
        print("===== SOURCES =====")

        for source in result.sources:
            print(
                source.index,
                source.source,
                source.domain,
                source.url,
            )


if __name__ == "__main__":
    main()
