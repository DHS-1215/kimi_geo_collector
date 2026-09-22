from playwright.sync_api import (
    sync_playwright,
)

from app.kimi.extractor import (
    KimiSourceExtractor,
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

        extractor = KimiSourceExtractor(
            page
        )

        sources = extractor.extract()

        print(
            "SOURCE COUNT:",
            len(sources)
        )

        for source in sources:

            print()
            print(
                "=" * 60
            )

            print(
                "INDEX:",
                source.index
            )

            print(
                "SOURCE:",
                source.source
            )

            print(
                "TITLE:",
                source.title
            )

            print(
                "URL:",
                source.url
            )

            print(
                "DOMAIN:",
                source.domain
            )

            print(
                "DESCRIPTION:"
            )

            print(
                source.description
            )


if __name__ == "__main__":
    main()