import json
from pathlib import Path

from app.kimi.exporter import KimiExporter
from app.kimi.result import KimiCollectionResult


def build_result(
        product: str,
        batch_id: str,
) -> KimiCollectionResult:
    return KimiCollectionResult(
        question="测试问题",
        answer="测试回答",
        model="快速",
        mode="标准",
        conversation_url=(
            "https://www.kimi.com/chat/test"
        ),
        sources=[],
        status="success",
        task_id="kimi_t_test",
        question_id="kimiq_001_test",
        mode_code="quick",
        batch_id=batch_id,
        product=product,
        acquisition_status="success",
        validation_status="NOT_APPLICABLE",
        is_complete=True,
        source_collection_status="success",
        source_count_raw=0,
        collected_at=(
            "2026-09-16T00:00:00+00:00"
        ),
    )


def test_export_tianyishou_manifest(
        tmp_path: Path,
):
    batch_id = (
        "kimi_tianyishou_test_001"
    )

    result = build_result(
        product="天益寿气血固本",
        batch_id=batch_id,
    )

    output_dir = (
            tmp_path
            / "package"
    )

    KimiExporter().export(
        results=[result],
        output_dir=str(output_dir),
    )

    manifest = json.loads(
        (
                output_dir
                / "manifest.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
            manifest["product_id"]
            == "tianyishou_qixueguben"
    )

    assert (
            manifest["product_name"]
            == "天益寿气血固本"
    )

    assert (
            manifest["batch_id"]
            == batch_id
    )

    assert manifest["task_count"] == 1
    assert manifest["answer_count"] == 1
    assert manifest["source_count"] == 0
    assert manifest["status"] == "PASS"


def test_export_standard_files(
        tmp_path: Path,
):
    result = build_result(
        product="鸿茅药酒",
        batch_id="kimi_hongmao_test_001",
    )

    output_dir = (
            tmp_path
            / "package"
    )

    KimiExporter().export(
        results=[result],
        output_dir=str(output_dir),
    )

    expected_files = {
        "manifest.json",
        "tasks.jsonl",
        "answers.jsonl",
        "sources.jsonl",
        "checksums.json",
    }

    actual_files = {
        path.name
        for path in output_dir.iterdir()
        if path.is_file()
    }

    assert actual_files == expected_files
