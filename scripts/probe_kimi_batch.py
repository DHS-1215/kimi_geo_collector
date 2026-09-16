from pathlib import Path

from playwright.sync_api import sync_playwright

from app.kimi.checkpoint import (
    KimiCheckpointStore,
)
from app.kimi.client import KimiClient
from app.kimi.loader import load_questions
from app.kimi.runner import (
    KimiBatchRunner,
    build_geo_tasks,
)


CDP_URL = "http://127.0.0.1:9224"

CSV_PATH = (
    Path("input")
    / "kimi_w6_smoke.csv"
)

CHECKPOINT_ROOT = (
    Path("output")
    / "checkpoints"
)

BATCH_ID = "kimi_w6_delay_regression_001"


def main() -> None:
    questions = load_questions(
        str(CSV_PATH)
    )

    # 第一轮只取第 1 道题
    questions = questions[:2]

    tasks = build_geo_tasks(
        questions
    )

    print(
        f"QUESTIONS: {len(questions)}"
    )
    print(
        f"TASKS: {len(tasks)}"
    )

    checkpoint_store = (
        KimiCheckpointStore(
            root_dir=CHECKPOINT_ROOT,
            batch_id=BATCH_ID,
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
            page
            for page in pages
            if "kimi.com" in page.url.lower()
        )

        client = KimiClient(
            page=page
        )

        runner = KimiBatchRunner(
            client=client,
            batch_id=BATCH_ID,
            product="鸿茅药酒",
            checkpoint_store=(
                checkpoint_store
            ),
        )

        results = runner.run(
            tasks
        )

        print()
        print("=" * 60)
        print("BATCH RESULT")
        print("=" * 60)

        for result in results:
            print(
                result.task_id,
                result.model,
                result.mode,
                result.status,
                result.is_complete,
                len(result.answer),
                len(result.sources),
            )


if __name__ == "__main__":
    main()