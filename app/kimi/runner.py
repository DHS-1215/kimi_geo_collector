from __future__ import annotations

import random
import time
from dataclasses import dataclass

from app.kimi.client import KimiClient
from app.kimi.result import (
    KimiCollectionResult,
    utc_now_iso,
)
from app.kimi.types import (
    MODEL_MODE_COMPATIBILITY,
    KimiMode,
    KimiModel,
)

from app.kimi.geo_contract import (
    build_task_id,
    to_geo_mode,
)
from app.kimi.checkpoint import (
    KimiCheckpointStore,
)


@dataclass(frozen=True)
class KimiQuestion:
    question_id: str
    question: str


@dataclass
class KimiTask:
    question_id: str
    question: str
    model: KimiModel
    mode: KimiMode
    task_id: str = ""


def build_geo_tasks(
        questions: list[KimiQuestion],
        model: KimiModel = KimiModel.FAST,
        modes: tuple[KimiMode, ...] = (
                KimiMode.STANDARD,
                KimiMode.ADVANCED,
        ),
) -> list[KimiTask]:
    tasks: list[KimiTask] = []

    if model != KimiModel.FAST:
        raise ValueError(
            "KIMI GEO正式采集仅支持快速模型"
        )

    supported_modes = (
        MODEL_MODE_COMPATIBILITY[model]
    )

    for mode in modes:
        # 同时验证：
        # 1. 是否属于 GEO v1 正式模式
        # 2. 当前模型是否支持该模式
        to_geo_mode(mode)

        if mode not in supported_modes:
            raise ValueError(
                "KIMI不支持该模型/模式组合："
                f"{model.value} + {mode.value}"
            )

    for question in questions:
        for mode in modes:
            tasks.append(
                KimiTask(
                    question_id=question.question_id,
                    question=question.question,
                    model=model,
                    mode=mode,
                )
            )

    return tasks


class KimiBatchRunner:

    def __init__(
            self,
            client: KimiClient,
            batch_id: str,
            product: str,
            checkpoint_store: (
                    KimiCheckpointStore
                    | None
            ) = None,
    ):
        self.client = client
        self.config = client.config
        self.batch_id = batch_id
        self.product = product

        self.checkpoint_store = (
            checkpoint_store
        )

        self.started_at = ""
        self.finished_at = ""

    def prepare_task_identity(
            self,
            task: KimiTask,
    ) -> str:

        mode_code = to_geo_mode(
            task.mode
        )

        task.task_id = build_task_id(
            batch_id=self.batch_id,
            question_id=task.question_id,
            mode_code=mode_code,
        )

        return mode_code

    def run_task(
            self,
            task: KimiTask,
    ) -> KimiCollectionResult:

        mode_code = (
            self.prepare_task_identity(
                task
            )
        )

        result = self.client.collect(
            question=task.question,
            model=task.model,
            mode=task.mode,
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
            self.batch_id
        )

        result.product = (
            self.product
        )

        result.platform = "kimi"

        if (
                result.status == "success"
                and result.is_complete
        ):
            capture_screenshot = getattr(
                self.client,
                "capture_task_screenshot",
                None,
            )

            if capture_screenshot is not None:
                try:
                    screenshot = (
                        capture_screenshot(
                            task_id=task.task_id,
                            batch_id=self.batch_id,
                            source_count=result.source_count_raw,
                        )
                    )

                    result.screenshot_local_path = (
                        screenshot.get(
                            "local_path",
                            "",
                        )
                    )

                    result.screenshot_path = (
                        screenshot.get(
                            "path",
                            "",
                        )
                    )

                    result.screenshot_sha256 = (
                        screenshot.get(
                            "sha256",
                            "",
                        )
                    )

                    result.screenshot_size_bytes = (
                        screenshot.get(
                            "size_bytes",
                            0,
                        )
                    )

                    result.screenshot_width = (
                        screenshot.get(
                            "width",
                            0,
                        )
                    )

                    result.screenshot_height = (
                        screenshot.get(
                            "height",
                            0,
                        )
                    )

                    result.screenshot_error = (
                        screenshot.get(
                            "error",
                            "",
                        )
                    )

                except Exception as e:
                    result.screenshot_error = str(e)

        return result

    def run_task_with_retry(
            self,
            task: KimiTask,
    ) -> KimiCollectionResult:

        ordinary_retries_used = 0
        risk_retries_used = 0
        attempt = 0

        last_result: (
                KimiCollectionResult
                | None
        ) = None

        while True:
            attempt += 1

            try:
                result = self.run_task(
                    task
                )

            except Exception as e:
                # 最后一层 runner 兜底。
                # KeyboardInterrupt 属于 BaseException，
                # 不会在这里被吞掉。
                mode_code = (
                    self.prepare_task_identity(
                        task
                    )
                )

                page = getattr(
                    self.client,
                    "page",
                    None,
                )

                conversation_url = getattr(
                    page,
                    "url",
                    "",
                )

                result = KimiCollectionResult(
                    question=task.question,
                    answer="",
                    model=task.model.value,
                    mode=task.mode.value,
                    conversation_url=(
                        conversation_url
                    ),
                    sources=[],
                    status="failed",
                    error=(
                        "Runner 未捕获异常："
                        f"{e}"
                    ),
                    task_id=task.task_id,
                    question_id=(
                        task.question_id
                    ),
                    mode_code=mode_code,
                    batch_id=self.batch_id,
                    product=self.product,
                    platform="kimi",
                    acquisition_status="failed",
                    validation_status=(
                        "NOT_APPLICABLE"
                    ),
                    is_complete=False,
                    source_collection_status=(
                        "failed"
                    ),
                    source_count_raw=0,
                    collected_at=utc_now_iso(),
                )

            last_result = result

            succeeded = (
                    result.status == "success"
                    and result.is_complete
            )

            if succeeded:
                if attempt > 1:
                    print(
                        f"[RETRY] 第 {attempt} "
                        "次尝试成功"
                    )

                return result

            error_message = (
                    result.error
                    or "采集结果不完整"
            )

            is_capacity_limited = (
                    result.acquisition_status
                    == "service_capacity_limited"
            )

            if is_capacity_limited:
                print(
                    "[CAPACITY] "
                    "检测到KIMI服务容量限制："
                    f"{error_message}"
                )

                print(
                    "[CAPACITY] "
                    "当前任务停止重试，"
                    "避免继续请求页面"
                )

                return result

            is_risk_control = (
                    result.acquisition_status
                    == "risk_control"
            )

            if is_risk_control:
                print(
                    "[RISK CONTROL] "
                    f"检测到风控：{error_message}"
                )

                max_risk_retries = max(
                    0,
                    getattr(
                        self.config,
                        "risk_control_retry_max",
                        1,
                    ),
                )

                if (
                        risk_retries_used
                        >= max_risk_retries
                ):
                    print(
                        "[RISK CONTROL] "
                        "已达到最大恢复次数，"
                        "停止继续撞击页面"
                    )

                    return result

                risk_retries_used += 1

                delay = random.uniform(
                    getattr(
                        self.config,
                        "risk_control_delay_min",
                        60.0,
                    ),
                    getattr(
                        self.config,
                        "risk_control_delay_max",
                        120.0,
                    ),
                )

                print(
                    "[RISK CONTROL] "
                    f"进入冷却 {delay:.1f}s"
                )

                print(
                    "[RISK CONTROL] "
                    f"冷却后进行第 "
                    f"{risk_retries_used}/"
                    f"{max_risk_retries} "
                    "次恢复尝试"
                )

                time.sleep(
                    delay
                )

                recovery = getattr(
                    self.client,
                    "recover_after_risk_control",
                    None,
                )

                if recovery is not None:
                    try:
                        recovered = bool(
                            recovery()
                        )

                    except Exception as e:
                        print(
                            "[RISK CONTROL] "
                            "页面恢复检查异常："
                            f"{e}"
                        )

                        recovered = False

                    if not recovered:
                        print(
                            "[RISK CONTROL] "
                            "页面仍未恢复，"
                            "停止当前任务继续请求"
                        )

                        return result

                    print(
                        "[RISK CONTROL] "
                        "页面状态已恢复，"
                        "准备重新执行当前任务"
                    )

                continue

            print(
                f"[RETRY] 第 {attempt} "
                f"次尝试失败："
                f"{error_message}"
            )

            max_ordinary_retries = max(
                0,
                self.config.task_retry_max,
            )

            if (
                    ordinary_retries_used
                    >= max_ordinary_retries
            ):
                print(
                    "[RETRY] "
                    "已达到最大普通重试次数，"
                    "当前任务保留为 failed"
                )

                return result

            ordinary_retries_used += 1

            delay = random.uniform(
                self.config.task_retry_delay_min,
                self.config.task_retry_delay_max,
            )

            print(
                f"[RETRY] 等待 "
                f"{delay:.1f}s 后重试"
            )

            print(
                f"[RETRY] 准备进行第 "
                f"{ordinary_retries_used}/"
                f"{max_ordinary_retries} "
                "次普通重试"
            )

            time.sleep(
                delay
            )

        assert last_result is not None

    def run(
            self,
            tasks: list[KimiTask],
    ) -> list[KimiCollectionResult]:

        results: list[
            KimiCollectionResult
        ] = []

        if self.checkpoint_store:
            self.started_at = (
                self.checkpoint_store
                .initialize(
                    product=self.product,
                    planned_count=len(tasks),
                )
            )


        else:

            self.started_at = (

                utc_now_iso()

            )

        capacity_interrupted = False

        try:

            for index, task in enumerate(

                    tasks

            ):
                print(
                    "=" * 80
                )

                print(
                    f"[TASK "
                    f"{index + 1}/"
                    f"{len(tasks)}]"
                )

                print(
                    task.question
                )

                self.prepare_task_identity(
                    task
                )

                cached_result = None

                if self.checkpoint_store:
                    cached_result = (
                        self.checkpoint_store
                        .load_result(
                            task.task_id
                        )
                    )

                if (
                        cached_result
                        is not None
                        and
                        cached_result.status
                        == "success"
                        and
                        cached_result.is_complete
                ):
                    print(
                        "[CHECKPOINT] "
                        "已有成功结果，跳过"
                    )

                    print(
                        f"STATUS: "
                        f"{cached_result.status}"
                    )

                    results.append(
                        cached_result
                    )

                    continue

                result = (
                    self.run_task_with_retry(
                        task
                    )
                )

                results.append(
                    result
                )

                if self.checkpoint_store:
                    self.checkpoint_store.save_result(
                        result
                    )

                    print(
                        "[CHECKPOINT] "
                        "结果已保存"
                    )

                print(
                    f"STATUS: {result.status}"
                )

                if (
                        result.status == "failed"
                        and result.error
                ):
                    print(
                        f"ERROR: {result.error}"
                    )

                if (
                        result.acquisition_status
                        == "service_capacity_limited"
                ):
                    print(
                        "[CAPACITY] "
                        "检测到KIMI服务容量限制，"
                        "暂停整个批次"
                    )

                    capacity_interrupted = True
                    break

                if index < len(tasks) - 1:
                    time.sleep(
                        random.uniform(
                            self.config.task_delay_min,
                            self.config.task_delay_max,
                        )
                    )

            self.finished_at = (
                utc_now_iso()
            )

            if self.checkpoint_store:
                if capacity_interrupted:
                    self.checkpoint_store.mark_interrupted(
                        finished_at=(
                            self.finished_at
                        )
                    )

                else:
                    self.checkpoint_store.mark_completed(
                        results=results,
                        finished_at=(
                            self.finished_at
                        ),
                    )

            return results

        except BaseException:
            self.finished_at = (
                utc_now_iso()
            )

            if self.checkpoint_store:
                (
                    self.checkpoint_store
                    .mark_interrupted(
                        finished_at=(
                            self.finished_at
                        )
                    )
                )

            raise
