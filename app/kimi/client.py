from __future__ import annotations

from app.kimi.answer import (
    wait_for_answer,
)
from app.kimi.capacity import (
    is_service_capacity_limited,
)

from app.kimi.risk_control import (
    find_risk_control_marker,
)

import random
import time

from playwright.sync_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from .config import KimiConfig

from app.kimi.selectors import (
    INPUT_SELECTOR,
    SEND_SELECTOR,

    MODEL_SWITCH_SELECTOR,
    MODEL_OPTION_SELECTOR,
    MODEL_NAME_SELECTOR,
    CURRENT_EFFORT_SELECTOR,

    EFFORT_ENTRY_SELECTOR,
    EFFORT_OPTION_SELECTOR,
    EFFORT_NAME_SELECTOR,
    EFFORT_VALUE_SELECTOR,

    QUESTION_ITEM_SELECTOR,
    ASSISTANT_ITEM_SELECTOR,
)

from app.kimi.types import (
    MODEL_MODE_COMPATIBILITY,
    KimiMode,
    KimiModel,
)

from app.kimi.result import (
    KimiCollectionResult,
    utc_now_iso,
)

from app.kimi.source import KimiSource

from app.kimi.extractor import KimiSourceExtractor

from app.kimi.risk_control import (
    find_risk_control_marker,
)

from app.kimi.selectors import (
    ASSISTANT_ITEM_SELECTOR,
    INPUT_SELECTOR,
    MODEL_MENU_SELECTOR,
    MODEL_SWITCH_SELECTOR,
    MODE_OPTION_SELECTOR,
    NEW_CHAT_SELECTOR,
    QUESTION_ITEM_SELECTOR,
    REFERENCE_CLOSE_SELECTOR,
    REFERENCE_DRAWER_SELECTOR,
    REFERENCE_ITEM_SELECTOR,
    SEND_SELECTOR,
    SOURCE_TOOL_SELECTOR,
)


class KimiClient:
    def __init__(
            self,
            page: Page,
            answer_timeout_seconds: float | None = None,
            config: KimiConfig | None = None,
    ) -> None:
        self.page = page
        self.config = config or KimiConfig()

        self.answer_timeout_seconds = (
            float(answer_timeout_seconds)
            if answer_timeout_seconds is not None
            else float(self.config.answer_timeout)
        )

    def ask(self, question: str) -> str:
        question = question.strip()

        if not question:
            raise ValueError("question 不能为空")

        before_answer_count = self._answer_count()

        self._fill_question(question)
        self._send()

        answer = self._wait_for_new_answer_complete(
            before_answer_count=before_answer_count,
        )

        return answer

    def detect_risk_control(
            self,
            error_message: str = "",
    ) -> str | None:

        marker = find_risk_control_marker(
            error_message
        )

        if marker:
            return marker

        try:
            body_text = (
                self.page
                .locator("body")
                .inner_text(
                    timeout=1000
                )
            )

        except Exception:
            return None

        return find_risk_control_marker(
            body_text
        )

    def detect_service_capacity_limit(
            self,
            error_message: str = "",
    ) -> str | None:

        if is_service_capacity_limited(
                error_message
        ):
            return "service_capacity_limited"

        try:
            body_text = (
                self.page
                .locator("body")
                .inner_text(
                    timeout=1000
                )
            )

        except Exception:
            return None

        if is_service_capacity_limited(
                body_text
        ):
            return "service_capacity_limited"

        return None

    def recover_after_risk_control(
            self,
    ) -> bool:
        """
        风控冷却结束后的页面恢复检查。

        这里只做正常页面恢复：
        1. 检查页面是否仍可用
        2. 清理残留菜单 / 信源抽屉
        3. 检查是否仍存在明确风控提示
        4. 检查输入框
        5. 必要时最多刷新页面一次

        不处理验证码，也不绕过平台限制。
        """

        if self.page.is_closed():
            return False

        # 先尽量清理残留 UI。
        try:
            self._close_sources()
        except Exception:
            pass

        try:
            self._close_profile_menu()
        except Exception:
            pass

        # 风控提示如果仍然存在，
        # 当前页面就不应该继续发送请求。
        risk_marker = (
            self.detect_risk_control()
        )

        if risk_marker:
            print(
                "[RISK CONTROL] "
                "冷却后页面仍存在风控提示："
                f"{risk_marker}"
            )

            return False

        if self._input_is_ready():
            return True

        print(
            "[RISK CONTROL] "
            "输入区域尚未恢复，"
            "尝试刷新页面一次"
        )

        try:
            self.page.reload(
                wait_until="domcontentloaded",
                timeout=10000,
            )

        except Exception as e:
            print(
                "[RISK CONTROL] "
                f"页面刷新失败：{e}"
            )

            return False

        try:
            self.page.wait_for_timeout(
                1000
            )

        except Exception:
            return False

        # 刷新后重新检查风控，
        # 避免页面虽然能打开，
        # 但仍然处于限制状态。
        risk_marker = (
            self.detect_risk_control()
        )

        if risk_marker:
            print(
                "[RISK CONTROL] "
                "页面刷新后仍存在风控提示："
                f"{risk_marker}"
            )

            return False

        return self._input_is_ready()

    def _input_is_ready(
            self,
    ) -> bool:

        try:
            editor = self.page.locator(
                INPUT_SELECTOR
            ).first

            if editor.count() == 0:
                return False

            return editor.is_visible()

        except Exception:
            return False

    def collect(
            self,
            question: str,
            model: KimiModel,
            mode: KimiMode,
    ) -> KimiCollectionResult:

        try:
            self.new_chat()

            self.set_profile(
                model=model,
                mode=mode,
            )

            answer = self.ask(
                question
            )

        except Exception as e:

            error_message = str(e)

            capacity_status = (
                self.detect_service_capacity_limit(
                    error_message
                )
            )

            if capacity_status:
                acquisition_status = (
                    "service_capacity_limited"
                )

                capacity_message = (
                    "检测到KIMI服务容量限制："
                    "service_capacity_limited"
                )

                if error_message:
                    error_message = (
                        f"{error_message} | "
                        f"{capacity_message}"
                    )
                else:
                    error_message = (
                        capacity_message
                    )

            else:
                risk_marker = (
                    self.detect_risk_control(
                        error_message
                    )
                )

                if risk_marker:
                    acquisition_status = (
                        "risk_control"
                    )

                    risk_message = (
                        "检测到KIMI风控："
                        f"{risk_marker}"
                    )

                    if error_message:
                        error_message = (
                            f"{error_message} | "
                            f"{risk_message}"
                        )
                    else:
                        error_message = (
                            risk_message
                        )

                else:
                    acquisition_status = (
                        "failed"
                    )

            return KimiCollectionResult(
                question=question,
                answer="",
                model=model.value,
                mode=mode.value,
                conversation_url=self.page.url,
                sources=[],
                status="failed",
                error=error_message,
                acquisition_status=(
                    acquisition_status
                ),
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

        source_collection_status = "success"
        source_error = ""

        try:
            sources = self.get_sources()

        except Exception as e:
            sources = []
            source_collection_status = "failed"
            source_error = str(e)

        return KimiCollectionResult(
            question=question,
            answer=answer,
            model=model.value,
            mode=mode.value,
            conversation_url=self.page.url,
            sources=sources,
            status="success",
            acquisition_status="success",
            validation_status="NOT_APPLICABLE",
            is_complete=bool(
                answer.strip()
            ),
            source_collection_status=(
                source_collection_status
            ),
            source_count_raw=len(
                sources
            ),
            source_error=source_error,
            collected_at=utc_now_iso(),
        )

    def _fill_question(
            self,
            question: str,
    ) -> None:

        self._close_profile_menu()

        editor = self.page.locator(
            INPUT_SELECTOR
        ).first

        editor.wait_for(
            state="visible",
            timeout=5000,
        )

        editor.click(
            force=True
        )

        self._random_action_delay()

        editor.fill(
            question
        )

        self._random_action_delay()

    def _send(self) -> None:
        send_button = self.page.locator(
            SEND_SELECTOR
        ).first

        send_button.wait_for(
            state="visible",
            timeout=5000,
        )

        send_button.click()
        self._random_action_delay()

    def _answer_count(self) -> int:
        return self.page.locator(
            ASSISTANT_ITEM_SELECTOR
        ).count()

    def _wait_for_new_answer_complete(
            self,
            before_answer_count: int,
    ) -> str:
        return wait_for_answer(
            self.page,
            before_answer_count,
            timeout=self.answer_timeout_seconds,
            poll_interval=self.config.answer_poll_interval,
            stable_seconds=self.config.answer_stable_seconds,
        )

    def new_chat(self) -> None:
        new_chat_button = self.page.locator(
            NEW_CHAT_SELECTOR
        ).first

        new_chat_button.wait_for(
            state="visible",
            timeout=5000,
        )

        new_chat_button.click()
        self._random_action_delay()
        deadline = time.monotonic() + 10.0

        while time.monotonic() < deadline:
            question_count = self.page.locator(
                QUESTION_ITEM_SELECTOR
            ).count()

            answer_count = self.page.locator(
                ASSISTANT_ITEM_SELECTOR
            ).count()

            editor = self.page.locator(
                INPUT_SELECTOR
            ).first

            editor_visible = (
                    editor.count() > 0
                    and editor.is_visible()
            )

            if (
                    question_count == 0
                    and answer_count == 0
                    and editor_visible
            ):
                return

            self.page.wait_for_timeout(200)

        raise TimeoutError(
            "等待KIMI进入新对话超时"
        )

    def _current_model(
            self,
    ) -> str:
        trigger = self.page.locator(
            MODEL_SWITCH_SELECTOR
        ).first

        trigger.wait_for(
            state="visible",
            timeout=5000,
        )

        name_node = trigger.locator(
            MODEL_NAME_SELECTOR
        ).first

        if name_node.count() == 0:
            return ""

        return (
            name_node
            .inner_text()
            .strip()
        )

    def _current_mode(
            self,
    ) -> str:
        trigger = self.page.locator(
            MODEL_SWITCH_SELECTOR
        ).first

        trigger.wait_for(
            state="visible",
            timeout=5000,
        )

        effort_node = trigger.locator(
            CURRENT_EFFORT_SELECTOR
        ).first

        if effort_node.count() == 0:
            return ""

        return (
            effort_node
            .inner_text()
            .strip()
        )

    def _open_main_menu(
            self,
    ) -> None:
        trigger = self.page.locator(
            MODEL_SWITCH_SELECTOR
        ).first

        trigger.wait_for(
            state="visible",
            timeout=5000,
        )

        if (
                trigger.get_attribute(
                    "aria-expanded"
                )
                == "true"
        ):
            return

        trigger.click()
        self._random_action_delay()

        deadline = (
                time.monotonic()
                + 5.0
        )

        while (
                time.monotonic()
                < deadline
        ):
            trigger = self.page.locator(
                MODEL_SWITCH_SELECTOR
            ).first

            if (
                    trigger.count() > 0
                    and trigger.get_attribute(
                "aria-expanded"
            )
                    == "true"
            ):
                return

            self.page.wait_for_timeout(
                100
            )

        raise TimeoutError(
            "等待KIMI模型菜单打开超时"
        )

    def set_model(
            self,
            model: KimiModel,
    ) -> None:
        current = self._current_model()

        if current == model.value:
            return

        self._open_main_menu()

        options = self.page.locator(
            MODEL_OPTION_SELECTOR
        )

        target = None

        for index in range(
                options.count()
        ):
            option = options.nth(
                index
            )

            name_node = option.locator(
                MODEL_NAME_SELECTOR
            ).first

            if name_node.count() == 0:
                continue

            name = (
                name_node
                .inner_text()
                .strip()
            )

            if name == model.value:
                target = option
                break

        if target is None:
            self._close_profile_menu()

            raise RuntimeError(
                "没有找到KIMI模型："
                f"{model.value}"
            )

        if (
                target.get_attribute(
                    "aria-checked"
                )
                != "true"
        ):
            target.click()
            self._random_action_delay()

        # K3 / K3集群切换会发生页面路由变化，
        # 所以不能继续使用点击前的旧 locator。
        deadline = (
                time.monotonic()
                + 10.0
        )

        while (
                time.monotonic()
                < deadline
        ):
            try:
                current = (
                    self._current_model()
                )

                if current == model.value:
                    return

            except Exception:
                pass

            self.page.wait_for_timeout(
                150
            )

        raise TimeoutError(
            "KIMI模型切换失败："
            f"{model.value}"
        )

    def set_mode(
            self,
            mode: KimiMode,
    ) -> None:
        current = self._current_mode()

        if current == mode.value:
            return

        self._open_main_menu()

        effort_entry = self.page.locator(
            EFFORT_ENTRY_SELECTOR
        ).first

        effort_entry.wait_for(
            state="visible",
            timeout=5000,
        )

        if (
                effort_entry.get_attribute(
                    "aria-expanded"
                )
                != "true"
        ):
            effort_entry.click()
            self._random_action_delay()

        options = self.page.locator(
            EFFORT_OPTION_SELECTOR
        )

        options.first.wait_for(
            state="visible",
            timeout=5000,
        )

        target = None

        for index in range(
                options.count()
        ):
            option = options.nth(
                index
            )

            name_node = option.locator(
                EFFORT_NAME_SELECTOR
            ).first

            if name_node.count() == 0:
                continue

            name = (
                name_node
                .inner_text()
                .strip()
            )

            if name == mode.value:
                target = option
                break

        if target is None:
            self._close_profile_menu()

            raise RuntimeError(
                "当前KIMI模型没有思考强度："
                f"{mode.value}"
            )

        if (
                target.get_attribute(
                    "aria-checked"
                )
                != "true"
        ):
            target.click()
            self._random_action_delay()

        deadline = (
                time.monotonic()
                + 5.0
        )

        while (
                time.monotonic()
                < deadline
        ):
            try:
                current = (
                    self._current_mode()
                )

                if current == mode.value:
                    return

            except Exception:
                pass

            self.page.wait_for_timeout(
                100
            )

        raise TimeoutError(
            "KIMI思考强度切换失败："
            f"{mode.value}"
        )

    def set_profile(
            self,
            model: KimiModel,
            mode: KimiMode,
    ) -> None:
        supported_modes = (
            MODEL_MODE_COMPATIBILITY[
                model
            ]
        )

        if mode not in supported_modes:
            raise ValueError(
                "KIMI不支持该模型/思考强度组合："
                f"{model.value} + {mode.value}"
            )

        try:
            # 顺序非常重要：
            # 必须先切模型，再切思考强度。
            self.set_model(
                model
            )

            self.set_mode(
                mode
            )

            current_model = (
                self._current_model()
            )

            current_mode = (
                self._current_mode()
            )

            if (
                    current_model
                    != model.value
            ):
                raise RuntimeError(
                    "KIMI模型最终校验失败："
                    f"期望={model.value}，"
                    f"实际={current_model}"
                )

            if (
                    current_mode
                    != mode.value
            ):
                raise RuntimeError(
                    "KIMI思考强度最终校验失败："
                    f"期望={mode.value}，"
                    f"实际={current_mode}"
                )

        finally:
            self._close_profile_menu()

    def _close_profile_menu(
            self,
    ) -> None:
        # KIMI可能同时存在：
        # 主模型菜单 + 思考强度二级菜单。
        # 最多按两次 Escape 即可全部关闭。
        for _ in range(2):
            menus = self.page.locator(
                '.kimi-menu-positioner'
                '[role="menu"]:visible'
            )

            if menus.count() == 0:
                return

            self.page.keyboard.press(
                "Escape"
            )

            self.page.wait_for_timeout(
                100
            )

    def _open_sources(self) -> bool:
        tools = self.page.locator(
            SOURCE_TOOL_SELECTOR
        )

        visible_tool = None

        for index in range(tools.count()):
            item = tools.nth(index)

            if item.is_visible():
                visible_tool = item
                break

        if visible_tool is None:
            return False

        visible_tool.click()

        self._random_action_delay()

        drawer = self.page.locator(
            REFERENCE_DRAWER_SELECTOR
        ).first

        drawer.wait_for(
            state="visible",
            timeout=5000,
        )

        # Drawer 出现不代表引用卡片已经渲染完成。
        # 继续等待至少一条正式引用来源。
        first_item = self.page.locator(
            REFERENCE_ITEM_SELECTOR
        ).first

        first_item.wait_for(
            state="visible",
            timeout=5000,
        )

        return True

    def _close_sources(self) -> None:
        close_button = self.page.locator(
            REFERENCE_CLOSE_SELECTOR
        )

        if (
                close_button.count() > 0
                and close_button.first.is_visible()
        ):
            close_button.first.click()

            self._random_action_delay()

    def get_sources(
            self,
    ) -> list[KimiSource]:
        extractor = KimiSourceExtractor(
            page=self.page,
        )

        return extractor.extract()

    def _random_action_delay(
            self,
    ):
        time.sleep(
            random.uniform(
                self.config.action_delay_min,
                self.config.action_delay_max,
            )
        )
