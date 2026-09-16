from pathlib import Path

from app.kimi.checkpoint import KimiCheckpointStore
from app.kimi.config import KimiConfig
from app.kimi.result import (
    KimiCollectionResult,
    utc_now_iso,
)
from app.kimi.runner import (
    KimiBatchRunner,
    KimiTask,
)
from app.kimi.types import (
    KimiMode,
    KimiModel,
)


class FakeClient:
    def __init__(self):
        self.config = KimiConfig()


def build_result(
        task: KimiTask,
        *,
        success: bool,
        acquisition_status: str,
) -> KimiCollectionResult:
    return KimiCollectionResult(
        question=task.question,
        answer=(
            "probe success"
            if success
            else ""
        ),
        model=task.model.value,
        mode=task.mode.value,
        conversation_url="",
        sources=[],
        status=(
            "success"
            if success
            else "failed"
        ),
        error=(
            ""
            if success
            else "检测到KIMI服务容量限制"
        ),
        acquisition_status=(
            acquisition_status
        ),
        validation_status="NOT_APPLICABLE",
        is_complete=success,
        source_collection_status=(
            "success"
            if success
            else "failed"
        ),
        source_count_raw=0,
        collected_at=utc_now_iso(),
    )


def main():
    batch_id = "kimi_capacity_probe_001"

    checkpoint_store = KimiCheckpointStore(
        root_dir=Path("output") / "checkpoints",
        batch_id=batch_id,
    )

    runner = KimiBatchRunner(
        client=FakeClient(),
        batch_id=batch_id,
        product="鸿茅药酒",
        checkpoint_store=checkpoint_store,
    )

    tasks = [
        KimiTask(
            question_id=f"q{i}",
            question=f"测试问题{i}",
            model=KimiModel.FAST,
            mode=KimiMode.STANDARD,
        )
        for i in range(1, 5)
    ]

    executed = []

    def fake_run_task_with_retry(task):
        executed.append(
            task.question_id
        )

        if task.question_id == "q3":
            result = build_result(
                task,
                success=False,
                acquisition_status=(
                    "service_capacity_limited"
                ),
            )

        else:
            result = build_result(
                task,
                success=True,
                acquisition_status="success",
            )

        # synthetic probe 绕过了真实 run_task()，
        # 因此这里手动补齐真实链路会写入的任务身份字段。
        mode_code = (
            runner.prepare_task_identity(
                task
            )
        )

        result.question_id = (
            task.question_id
        )

        result.task_id = (
            task.task_id
        )

        result.mode_code = (
            mode_code
        )

        result.batch_id = (
            runner.batch_id
        )

        result.product = (
            runner.product
        )

        result.platform = "kimi"

        return result

    runner.run_task_with_retry = (
        fake_run_task_with_retry
    )

    results = runner.run(
        tasks
    )

    print()
    print("=" * 60)
    print("PROBE RESULT")
    print("=" * 60)
    print("EXECUTED:", executed)
    print("RESULT COUNT:", len(results))

    for result in results:
        print(
            result.question_id,
            result.status,
            result.acquisition_status,
        )


if __name__ == "__main__":
    main()
