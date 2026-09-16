from pathlib import Path

from app.kimi.checkpoint import (
    KimiCheckpointStore,
)


def test_interrupted_batch_can_resume(
        tmp_path: Path,
):
    root = (
            tmp_path
            / "checkpoints"
    )

    batch_id = (
        "kimi_resume_test_001"
    )

    store = KimiCheckpointStore(
        root_dir=root,
        batch_id=batch_id,
    )

    store.initialize(
        product="鸿茅药酒",
        planned_count=12,
    )

    store.mark_interrupted(
        finished_at=(
            "2026-09-16T00:00:00+00:00"
        )
    )

    resolved_batch_id, resumed = (
        KimiCheckpointStore
        .resolve_batch_id(
            root_dir=root,
            new_batch_id=(
                "kimi_new_batch_001"
            ),
        )
    )

    assert resumed is True

    assert (
            resolved_batch_id
            == batch_id
    )


def test_force_new_does_not_resume(
        tmp_path: Path,
):
    root = (
            tmp_path
            / "checkpoints"
    )

    old_batch_id = (
        "kimi_resume_test_002"
    )

    store = KimiCheckpointStore(
        root_dir=root,
        batch_id=old_batch_id,
    )

    store.initialize(
        product="鸿茅药酒",
        planned_count=12,
    )

    store.mark_interrupted(
        finished_at=(
            "2026-09-16T00:00:00+00:00"
        )
    )

    new_batch_id = (
        "kimi_new_batch_002"
    )

    resolved_batch_id, resumed = (
        KimiCheckpointStore
        .resolve_batch_id(
            root_dir=root,
            new_batch_id=new_batch_id,
            force_new=True,
        )
    )

    assert resumed is False

    assert (
            resolved_batch_id
            == new_batch_id
    )
