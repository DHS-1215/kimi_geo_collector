from __future__ import annotations
import os
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from app.kimi.checkpoint import KimiCheckpointStore
from app.kimi.client import KimiClient
from app.kimi.exporter import KimiExporter
from app.kimi.geo_contract import resolve_product
from app.kimi.loader import load_questions
from app.kimi.packager import create_package
from app.kimi.runner import (
    KimiBatchRunner,
    build_geo_tasks,
)

CDP_URL = "http://127.0.0.1:9224"

OUTPUT_ROOT = Path("output")
PACKAGE_ROOT = OUTPUT_ROOT / "package"

PRODUCT_OPTIONS = {
    "1": {
        "name": "鸿茅药酒",
        "csv": Path("input") / "hongmao_questions.csv",
    },
    "2": {
        "name": "天益寿气血固本",
        "csv": Path("input") / "tianyishou_questions.csv",
    },
}


def choose_product() -> tuple[str, str, Path]:
    print()
    print("=" * 60)
    print("KIMI GEO Collection Pipeline")
    print("=" * 60)
    print()
    print("请选择采集产品：")
    print()
    print("1. 鸿茅药酒")
    print("2. 天益寿气血固本")
    print()
    print("Q. 退出")
    print()

    while True:
        choice = input(
            "请输入选项 [1/2/Q]: "
        ).strip()

        if choice.upper() == "Q":
            raise SystemExit(0)

        option = PRODUCT_OPTIONS.get(
            choice
        )

        if option is None:
            print(
                "输入无效，请重新输入。"
            )
            continue

        product_name = option["name"]
        product_id, product_name = (
            resolve_product(
                product_name
            )
        )

        return (
            product_id,
            product_name,
            option["csv"],
        )


def main() -> None:
    (
        product_id,
        product_name,
        csv_path,
    ) = choose_product()

    if not csv_path.is_file():
        raise FileNotFoundError(
            f"题库不存在：{csv_path}"
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    new_batch_id = (
        f"kimi_{product_id}_{timestamp}"
    )

    checkpoint_root = (
            OUTPUT_ROOT
            / "checkpoints"
            / product_id
    )

    batch_id, resumed = (
        KimiCheckpointStore.resolve_batch_id(
            root_dir=checkpoint_root,
            new_batch_id=new_batch_id,
        )
    )

    print()
    print("=" * 60)
    print("任务信息")
    print("=" * 60)
    print()
    print(f"[PRODUCT]  {product_name}")
    print(f"[ID]       {product_id}")
    print(f"[CSV]      {csv_path.resolve()}")
    print(f"[BATCH]    {batch_id}")
    print(f"[RESUME]   {resumed}")
    print()

    questions = load_questions(
        str(csv_path)
    )

    question_limit = int(
        os.getenv(
            "KIMI_QUESTION_LIMIT",
            "0",
        )
    )

    if question_limit > 0:
        print()
        print(
            "[TEST MODE] "
            f"KIMI_QUESTION_LIMIT="
            f"{question_limit}"
        )
        print(
            "[TEST MODE] "
            "当前仅运行部分题目，"
            "不是正式全量采集。"
        )

        questions = questions[
                    :question_limit
                    ]

    tasks = build_geo_tasks(
        questions
    )

    print(
        f"[QUESTIONS] {len(questions)}"
    )
    print(
        f"[TASKS]     {len(tasks)}"
    )

    checkpoint_store = (
        KimiCheckpointStore(
            root_dir=checkpoint_root,
            batch_id=batch_id,
        )
    )

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
            (
                page
                for page in pages
                if "kimi.com"
                   in page.url.lower()
            ),
            None,
        )

        if page is None:
            raise RuntimeError(
                "CDP 中没有找到 KIMI 页面"
            )

        client = KimiClient(
            page=page
        )

        runner = KimiBatchRunner(
            client=client,
            batch_id=batch_id,
            product=product_name,
            checkpoint_store=(
                checkpoint_store
            ),
        )

        results = runner.run(
            tasks
        )

        capacity_interrupted = any(
            result.acquisition_status
            == "service_capacity_limited"
            for result in results
        )

        if capacity_interrupted:
            success_count = sum(
                1
                for result in results
                if (
                        result.status == "success"
                        and result.is_complete
                )
            )

            remaining_count = (
                    len(tasks)
                    - success_count
            )

            print()
            print("=" * 60)
            print("Pipeline Interrupted")
            print("=" * 60)
            print()
            print(
                f"[PRODUCT]   {product_name}"
            )
            print(
                f"[BATCH]     {batch_id}"
            )
            print(
                "[REASON]    "
                "KIMI 服务容量限制"
            )
            print(
                f"[TOTAL]     {len(tasks)}"
            )
            print(
                f"[SUCCESS]   {success_count}"
            )
            print(
                f"[REMAINING] {remaining_count}"
            )
            print()
            print(
                "[CHECKPOINT] 当前进度已保存"
            )
            print(
                "[ACTION]     请稍后重新运行"
                "并选择同一产品"
            )
            print(
                "[RESUME]     系统将自动续跑，"
                "已成功任务不会重复采集"
            )
            print(
                "[PACKAGE]    本次不生成最终 "
                "GEO 标准包和 ZIP"
            )

            return

    output_dir = (
            PACKAGE_ROOT
            / batch_id
    )

    exporter = KimiExporter()

    exporter.export(
        results=results,
        output_dir=str(output_dir),
        started_at=runner.started_at,
        finished_at=runner.finished_at,
    )

    zip_path = (
            PACKAGE_ROOT
            / f"{batch_id}.zip"
    )

    create_package(
        source_dir=output_dir,
        zip_path=zip_path,
    )

    success_count = sum(
        1
        for result in results
        if (
                result.status == "success"
                and result.is_complete
        )
    )

    failed_count = (
            len(tasks)
            - success_count
    )

    source_count = sum(
        len(result.sources)
        for result in results
    )

    print()
    print("=" * 60)
    print("Pipeline Finished")
    print("=" * 60)
    print()
    print(
        f"[PRODUCT]   {product_name}"
    )
    print(
        f"[BATCH]     {batch_id}"
    )
    print(
        f"[TASKS]     {len(tasks)}"
    )
    print(
        f"[SUCCESS]   {success_count}"
    )
    print(
        f"[FAILED]    {failed_count}"
    )
    print(
        f"[SOURCES]   {source_count}"
    )
    print()
    print(
        f"[PACKAGE]   {output_dir.resolve()}"
    )
    print(
        f"[ZIP]       {zip_path.resolve()}"
    )


if __name__ == "__main__":
    main()
