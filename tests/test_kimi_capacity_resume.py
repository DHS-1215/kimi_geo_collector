from types import SimpleNamespace

from scripts.run_kimi_pipeline import (
    run_with_capacity_resume,
)


def build_result(
        *,
        status: str,
        acquisition_status: str,
        is_complete: bool,
):
    return SimpleNamespace(
        status=status,
        acquisition_status=(
            acquisition_status
        ),
        is_complete=is_complete,
    )


class FakeRunner:
    def __init__(
            self,
            runs,
    ):
        self.runs = runs
        self.call_count = 0

    def run(
            self,
            tasks,
    ):
        result = self.runs[
            self.call_count
        ]

        self.call_count += 1

        return result


def test_capacity_resume_with_r(
        monkeypatch,
):
    first_run = [
        build_result(
            status="success",
            acquisition_status="success",
            is_complete=True,
        ),
        build_result(
            status="failed",
            acquisition_status=(
                "service_capacity_limited"
            ),
            is_complete=False,
        ),
    ]

    second_run = [
        build_result(
            status="success",
            acquisition_status="success",
            is_complete=True,
        ),
        build_result(
            status="success",
            acquisition_status="success",
            is_complete=True,
        ),
    ]

    runner = FakeRunner(
        runs=[
            first_run,
            second_run,
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "R",
    )

    results = run_with_capacity_resume(
        runner=runner,
        tasks=[
            "task_1",
            "task_2",
        ],
        product_name="鸿茅药酒",
        batch_id="kimi_test_001",
    )

    assert runner.call_count == 2
    assert results == second_run


def test_capacity_quit_with_q(
        monkeypatch,
):
    capacity_run = [
        build_result(
            status="failed",
            acquisition_status=(
                "service_capacity_limited"
            ),
            is_complete=False,
        ),
    ]

    runner = FakeRunner(
        runs=[
            capacity_run,
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "Q",
    )

    results = run_with_capacity_resume(
        runner=runner,
        tasks=[
            "task_1",
        ],
        product_name="鸿茅药酒",
        batch_id="kimi_test_002",
    )

    assert runner.call_count == 1
    assert results is None


def test_capacity_can_resume_multiple_times(
        monkeypatch,
):
    first_run = [
        build_result(
            status="failed",
            acquisition_status=(
                "service_capacity_limited"
            ),
            is_complete=False,
        ),
    ]

    second_run = [
        build_result(
            status="failed",
            acquisition_status=(
                "service_capacity_limited"
            ),
            is_complete=False,
        ),
    ]

    third_run = [
        build_result(
            status="success",
            acquisition_status="success",
            is_complete=True,
        ),
    ]

    runner = FakeRunner(
        runs=[
            first_run,
            second_run,
            third_run,
        ]
    )

    actions = iter([
        "R",
        "R",
    ])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(actions),
    )

    results = run_with_capacity_resume(
        runner=runner,
        tasks=[
            "task_1",
        ],
        product_name="鸿茅药酒",
        batch_id="kimi_test_003",
    )

    assert runner.call_count == 3
    assert results == third_run
