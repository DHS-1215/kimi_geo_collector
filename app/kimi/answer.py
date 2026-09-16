import time
from dataclasses import dataclass

from playwright.sync_api import Page

from collections.abc import Callable

from .selectors import ASSISTANT_ITEM_SELECTOR


@dataclass(frozen=True)
class KimiAssistantState:
    assistant_count: int
    thinking_state: str
    answer: str
    has_actions: bool
    is_capacity_waiting: bool


def read_latest_assistant_state(
        page: Page,
) -> KimiAssistantState:
    assistants = page.locator(
        ASSISTANT_ITEM_SELECTOR
    )

    assistant_count = assistants.count()

    if assistant_count == 0:
        return KimiAssistantState(
            assistant_count=0,
            thinking_state="",
            answer="",
            has_actions=False,
            is_capacity_waiting=False,
        )

    latest = assistants.last

    data = latest.evaluate(
        """
        root => {
            const allText = (
                root.innerText || ''
            ).trim();

            let thinkingState = '';

            if (
                allText.includes('正在思考中')
            ) {
                thinkingState = 'thinking';
            } else if (
                allText.includes('思考已完成')
            ) {
                thinkingState = 'done';
            }
            const isCapacityWaiting = (
            allText.includes('高峰期算力不足') ||
            allText.includes('请耐心等待')
            );

            const markdownContainers = [
                ...root.querySelectorAll(
                    '.markdown-container'
                )
            ];

            const answers = [];

            for (
                const container
                of markdownContainers
            ) {
                // 排除思考过程
                if (
                    container.closest(
                        '.thinking-container'
                    )
                ) {
                    continue;
                }

                const markdown =
                    container.querySelector(
                        '.markdown'
                    );

                if (!markdown) {
                    continue;
                }

                const text = (
                    markdown.innerText ||
                    markdown.textContent ||
                    ''
                ).trim();

                if (text) {
                    answers.push(text);
                }
            }

            return {
                thinking_state:
                    thinkingState,

                answer:
                    answers.length
                        ? answers[
                            answers.length - 1
                          ]
                        : '',

                has_actions:
                    Boolean(
                        root.querySelector(
                            '.segment-assistant-actions'
                        )
                    ),
                is_capacity_waiting:
                isCapacityWaiting
            };
        }
        """
    )

    return KimiAssistantState(
        assistant_count=assistant_count,
        thinking_state=(
            data["thinking_state"]
        ),
        answer=data["answer"],
        has_actions=data["has_actions"],
        is_capacity_waiting=(
            data["is_capacity_waiting"]
        ),
    )


def wait_for_answer(
        page: Page,
        previous_assistant_count: int,
        timeout: float = 120,
        poll_interval: float = 0.5,
        stable_seconds: float = 2.0,
        abort_check: (
                Callable[[], str | None]
                | None
        ) = None,
) -> str:
    deadline = (
            time.monotonic() + timeout
    )

    last_answer = ""

    stable_since: float | None = None

    while time.monotonic() < deadline:
        if abort_check is not None:
            abort_reason = abort_check()

            if abort_reason:
                raise RuntimeError(
                    abort_reason
                )
        state = (
            read_latest_assistant_state(
                page
            )
        )

        # 必须是新回答
        if (
                state.assistant_count
                <= previous_assistant_count
        ):
            time.sleep(poll_interval)
            continue

        answer = state.answer

        # 正文发生变化，重新计时
        if answer != last_answer:
            last_answer = answer

            if answer:
                stable_since = (
                    time.monotonic()
                )
            else:
                stable_since = None

        stable_for = 0.0

        if (
                answer
                and stable_since is not None
        ):
            stable_for = (
                    time.monotonic()
                    - stable_since
            )

        completed = (
                bool(answer)
                and (
                        state.thinking_state
                        != "thinking"
                )
                and not state.is_capacity_waiting
                and state.has_actions
                and (
                        stable_for
                        >= stable_seconds
                )
        )

        if completed:
            return answer

        time.sleep(poll_interval)

    raise TimeoutError(
        "等待 KIMI 回答完成超时"
    )
