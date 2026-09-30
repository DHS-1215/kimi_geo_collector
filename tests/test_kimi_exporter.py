import hashlib
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

    assert (
            manifest[
                "capabilities"
            ][
                "supports_screenshot"
            ]
            is True
    )

def test_export_screenshot_metadata_and_checksum(
        tmp_path: Path,
):
    batch_id = "kimi_hongmao_test_screenshot"

    result = build_result(
        product="鸿茅药酒",
        batch_id=batch_id,
    )

    screenshot_bytes = b"fake-kimi-screenshot"

    screenshot_source = (
            tmp_path
            / "collector_screenshot.png"
    )

    screenshot_source.write_bytes(
        screenshot_bytes
    )

    screenshot_sha256 = (
        hashlib.sha256(
            screenshot_bytes
        ).hexdigest()
    )

    result.screenshot_local_path = str(
        screenshot_source
    )

    result.screenshot_sha256 = (
        screenshot_sha256
    )

    result.screenshot_size_bytes = len(
        screenshot_bytes
    )

    result.screenshot_width = 2561
    result.screenshot_height = 1314

    output_dir = (
            tmp_path
            / "package"
    )

    KimiExporter().export(
        results=[result],
        output_dir=str(output_dir),
    )

    expected_screenshot_path = (
        "screenshots/kimi_t_test.png"
    )

    package_screenshot = (
            output_dir
            / "screenshots"
            / "kimi_t_test.png"
    )

    assert package_screenshot.is_file()

    assert (
            package_screenshot.read_bytes()
            == screenshot_bytes
    )

    answers = [
        json.loads(line)
        for line in (
                output_dir
                / "answers.jsonl"
        ).read_text(
            encoding="utf-8"
        ).splitlines()
    ]

    assert len(answers) == 1

    answer = answers[0]

    assert (
            answer["screenshot_path"]
            == expected_screenshot_path
    )

    platform_meta = (
        answer["platform_meta_json"]
    )

    assert (
            platform_meta[
                "screenshot_sha256"
            ]
            == screenshot_sha256
    )

    assert (
            platform_meta[
                "screenshot_size_bytes"
            ]
            == len(screenshot_bytes)
    )

    assert (
            platform_meta[
                "screenshot_width"
            ]
            == 2561
    )

    assert (
            platform_meta[
                "screenshot_height"
            ]
            == 1314
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
            manifest[
                "capabilities"
            ][
                "supports_screenshot"
            ]
            is True
    )

    checksums = json.loads(
        (
                output_dir
                / "checksums.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
            expected_screenshot_path
            in checksums["files"]
    )

    assert (
            checksums["files"][
                expected_screenshot_path
            ]
            == screenshot_sha256
    )

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
