from __future__ import annotations

from urllib.parse import (
    urldefrag,
    urlparse,
)

from playwright.sync_api import Page

from app.kimi.selectors import (
    ASSISTANT_ITEM_SELECTOR,
    CITATION_SELECTOR,
)

from app.kimi.source import KimiSource


class KimiSourceExtractor:

    def __init__(
            self,
            page: Page,
    ) -> None:
        self.page = page

    def extract(
            self,
    ) -> list[KimiSource]:

        assistants = self.page.locator(
            ASSISTANT_ITEM_SELECTOR
        )

        if assistants.count() == 0:
            return []

        latest = assistants.last

        citations = latest.locator(
            CITATION_SELECTOR
        )

        records: list[dict] = []

        url_positions: dict[str, int] = {}

        for citation_index in range(
                citations.count()
        ):
            citation = citations.nth(
                citation_index
            )

            raw_url = (
                    citation.get_attribute(
                        "href"
                    )
                    or ""
            ).strip()

            if not raw_url:
                continue

            # 去掉 #:~:text= 等 fragment
            clean_url, _ = urldefrag(
                raw_url
            )

            clean_url = clean_url.strip()

            if not clean_url:
                continue

            site_name = (
                    citation.get_attribute(
                        "data-site-name"
                    )
                    or ""
            ).strip()

            domain = urlparse(
                clean_url
            ).netloc

            if not site_name:
                site_name = domain

            context = citation.evaluate(
                """
                el => {
                    const paragraph =
                        el.closest('.paragraph');

                    if (!paragraph) {
                        return '';
                    }

                    return (
                        paragraph.innerText ||
                        paragraph.textContent ||
                        ''
                    ).trim();
                }
                """
            )

            context = (
                    context or ""
            ).strip()

            # 同一个网页已经出现过
            if clean_url in url_positions:

                position = url_positions[
                    clean_url
                ]

                contexts = records[
                    position
                ]["contexts"]

                if (
                        context
                        and context not in contexts
                ):
                    contexts.append(
                        context
                    )

                continue

            url_positions[
                clean_url
            ] = len(records)

            records.append(
                {
                    "source": site_name,
                    "url": clean_url,
                    "domain": domain,
                    "contexts": (
                        [context]
                        if context
                        else []
                    ),
                }
            )

        sources: list[KimiSource] = []

        for index, record in enumerate(
                records,
                start=1,
        ):
            description = "\n\n".join(
                record["contexts"]
            )

            sources.append(
                KimiSource(
                    index=index,
                    source=record["source"],

                    # 当前 KIMI 引用节点
                    # 不直接提供网页标题
                    title="",

                    description=description,
                    url=record["url"],
                    domain=record["domain"],
                )
            )

        return sources
