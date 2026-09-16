from types import SimpleNamespace

import pytest

from app.browser.cdp import (
    find_page_by_url,
)


def build_browser(
        urls: list[str],
):
    pages = [
        SimpleNamespace(
            url=url
        )
        for url in urls
    ]

    context = SimpleNamespace(
        pages=pages
    )

    return SimpleNamespace(
        contexts=[context]
    )


def test_find_kimi_chat_page():
    browser = build_browser(
        [
            "chrome://downloads",
            "https://example.com/",
            (
                "https://www.kimi.com/"
                "chat/test/123"
            ),
        ]
    )

    page = find_page_by_url(
        browser,
        "https://www.kimi.com/",
    )

    assert (
        page.url
        == (
            "https://www.kimi.com/"
            "chat/test/123"
        )
    )


def test_find_page_raises_when_missing():
    browser = build_browser(
        [
            "chrome://downloads",
            "https://example.com/",
        ]
    )

    with pytest.raises(
        RuntimeError,
        match="未找到目标页面",
    ):
        find_page_by_url(
            browser,
            "https://www.kimi.com/",
        )