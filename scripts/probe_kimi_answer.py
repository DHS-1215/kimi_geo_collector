import time

from playwright.sync_api import sync_playwright

CDP_URL = "http://127.0.0.1:9222"

INPUT_SELECTOR = (
    '.chat-input-editor'
    '[contenteditable="true"]'
    '[data-lexical-editor="true"]'
    '[role="textbox"]'
)

SEND_SELECTOR = ".send-button-container"

ASSISTANT_ITEM_SELECTOR = (
    ".chat-content-item-assistant"
)


def get_kimi_page(browser):
    pages = [
        page
        for context in browser.contexts
        for page in context.pages
    ]

    return next(
        page
        for page in pages
        if "kimi.com" in page.url.lower()
    )


def get_latest_assistant_state(page):
    assistants = page.locator(
        ASSISTANT_ITEM_SELECTOR
    )

    if assistants.count() == 0:
        return {
            "exists": False,
            "thinking_state": "",
            "answer": "",
            "has_actions": False,
        }

    latest = assistants.last

    return latest.evaluate(
        """
        root => {
            const allText = (
                root.innerText || ''
            ).trim();

            let thinkingState = '';

            if (allText.includes('正在思考中')) {
                thinkingState = 'thinking';
            } else if (
                allText.includes('思考已完成')
            ) {
                thinkingState = 'done';
            }

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
                // 排除思考区域
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

            const actions =
                root.querySelector(
                    '.segment-assistant-actions'
                );

            return {
                exists: true,
                thinking_state:
                    thinkingState,
                answer:
                    answers.length
                        ? answers[
                            answers.length - 1
                          ]
                        : '',
                answer_candidates:
                    answers,
                has_actions:
                    Boolean(actions),
            };
        }
        """
    )


def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(
            CDP_URL
        )

        page = get_kimi_page(browser)

        input_box = page.locator(
            INPUT_SELECTOR
        )

        send_button = page.locator(
            SEND_SELECTOR
        )

        question = (
            "什么是机器学习？"
            "请用三句话简单回答。"
        )

        old_count = page.locator(
            ASSISTANT_ITEM_SELECTOR
        ).count()

        print(
            "发送前 assistant 数量:",
            old_count,
        )

        input_box.click()
        input_box.fill(question)

        time.sleep(0.5)

        send_button.click()

        print("已发送:", question)

        last_answer = ""
        stable_count = 0

        for second in range(1, 61):
            time.sleep(1)

            count = page.locator(
                ASSISTANT_ITEM_SELECTOR
            ).count()

            state = (
                get_latest_assistant_state(
                    page
                )
            )

            answer = state["answer"]

            if (
                    answer and
                    answer == last_answer
            ):
                stable_count += 1
            else:
                stable_count = 0

            print(
                f"[{second:02d}s] "
                f"assistant={count} "
                f"thinking="
                f"{state['thinking_state']} "
                f"actions="
                f"{state['has_actions']} "
                f"stable="
                f"{stable_count}"
            )

            if answer:
                print(
                    "ANSWER:",
                    repr(answer)
                )

            # 第一版完成条件
            if (
                    count > old_count
                    and answer
                    and state["thinking_state"]
                    != "thinking"
                    and state["has_actions"]
                    and stable_count >= 2
            ):
                print(
                    "\n===== 回答完成 ====="
                )

                print(answer)

                return

            last_answer = answer

        raise TimeoutError(
            "等待 KIMI 回答完成超时"
        )


if __name__ == "__main__":
    main()
