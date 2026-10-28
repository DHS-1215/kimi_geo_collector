import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from app.kimi.client import KimiClient
from app.kimi.exporter import KimiExporter
from app.kimi.extractor import KimiSourceExtractor
from app.kimi.result import KimiCollectionResult
from app.kimi.source import KimiSource


def make_source(url, title=""):
    return KimiSource(
        index=1,
        source="测试网站",
        title=title,
        description="",
        url=url,
        domain="example.com",
    )


def make_panel_item(url, title):
    item = Mock()
    item.get_attribute.return_value = url

    title_node = item.locator.return_value.first
    title_node.count.return_value = 1
    title_node.inner_text.return_value = title

    return item


def test_title_matches_by_url_not_order():
    """面板顺序不同也能按 URL 正确关联标题。"""

    url_a = "https://example.com/a"
    url_b = "https://example.com/b"
    url_c = "https://example.com/c"

    sources = [
        make_source(url_a),
        make_source(url_b),
        make_source(url_c),
    ]

    items = Mock()
    items.count.return_value = 2
    items.nth.side_effect = [
        make_panel_item(url_b, "文章B"),
        make_panel_item(url_a + "#section", "文章A"),
    ]

    page = Mock()
    page.locator.return_value = items

    extractor = KimiSourceExtractor(page)
    result = extractor.enrich_titles_from_open_panel(
        sources
    )

    assert [s.title for s in result] == [
        "文章A",
        "文章B",
        "",
    ]

    # 没有修改原始来源对象
    assert sources[0].title == ""


def test_client_get_sources_enriches_titles():
    """get_sources 能打开面板并调用标题补全。"""

    source = make_source("https://example.com/a")
    enriched = replace(source, title="文章A")

    client = KimiClient(page=Mock())

    with patch(
        "app.kimi.client.KimiSourceExtractor"
    ) as extractor_class:
        extractor = extractor_class.return_value
        extractor.extract.return_value = [source]
        extractor.enrich_titles_from_open_panel.return_value = [
            enriched
        ]

        with patch.object(
            client, "_open_sources", return_value=True
        ) as open_panel, patch.object(
            client, "_close_sources"
        ) as close_panel:
            result = client.get_sources()

    assert result[0].title == "文章A"
    open_panel.assert_called_once()
    assert close_panel.call_count == 2
    extractor.enrich_titles_from_open_panel.assert_called_once_with(
        [source]
    )


def test_panel_failure_preserves_original_sources():
    """面板打不开也不能丢失原有来源。"""

    source = make_source("https://example.com/a")
    client = KimiClient(page=Mock())

    with patch(
        "app.kimi.client.KimiSourceExtractor"
    ) as extractor_class:
        extractor = extractor_class.return_value
        extractor.extract.return_value = [source]

        with patch.object(
            client, "_open_sources", return_value=False
        ), patch.object(client, "_close_sources"):
            result = client.get_sources()

        extractor.enrich_titles_from_open_panel.assert_not_called()

    assert result == [source]


def test_no_sources_does_not_open_panel():
    """无引用的回答不需要展开面板。"""

    client = KimiClient(page=Mock())

    with patch(
        "app.kimi.client.KimiSourceExtractor"
    ) as extractor_class:
        extractor_class.return_value.extract.return_value = []

        with patch.object(
            client, "_open_sources"
        ) as open_panel:
            result = client.get_sources()

    assert result == []
    open_panel.assert_not_called()


def test_exporter_writes_source_title(tmp_path: Path):
    """文章标题最终应进入 GEO 标准包。"""

    result = KimiCollectionResult(
        question="测试问题",
        answer="测试回答",
        model="快速",
        mode="标准",
        conversation_url="https://www.kimi.com/chat/test",
        sources=[
            make_source(
                "https://example.com/a",
                title="国家药品监督管理局新闻标题",
            )
        ],
        task_id="kimi_t_title_test",
        question_id="kimiq_title_test",
        mode_code="quick",
        batch_id="kimi_hongmao_title_test",
        product="鸿茅药酒",
        source_count_raw=1,
    )

    output_dir = tmp_path / "package"

    KimiExporter().export(
        results=[result],
        output_dir=str(output_dir),
    )

    rows = [
        json.loads(line)
        for line in (
            output_dir / "sources.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert len(rows) == 1
    assert rows[0]["source_title_raw"] == (
        "国家药品监督管理局新闻标题"
    )
