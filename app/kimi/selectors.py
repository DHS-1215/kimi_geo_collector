INPUT_SELECTOR = (
    '.chat-input-editor'
    '[contenteditable="true"]'
    '[data-lexical-editor="true"]'
    '[role="textbox"]'
)

SEND_SELECTOR = ".send-button-container"

MODEL_SWITCH_SELECTOR = ".current-model"

NEW_CHAT_SELECTOR = (
    'a[aria-label="新建会话"]'
    '[href*="chat_enter_method=new_chat"]'
)


MODE_OPTION_SELECTOR = (
    'button[role="menuitemradio"]'
)

MODEL_MENU_SELECTOR = (
    'button[role="menuitem"]'
    '[aria-label="选择模型"]'
)

SOURCE_TOOL_SELECTOR = (
    '[class*="ToolbarSearchGuid_searchGuidTool"]'
)

REFERENCE_DRAWER_SELECTOR = (
    ".agent-dialogue-references"
)

REFERENCE_ITEM_SELECTOR = (
    ".agent-dialogue-references__item"
)

REFERENCE_CARD_SELECTOR = (
    ".hyc-common-markdown__ref_card"
)

REFERENCE_SOURCE_SELECTOR = (
    ".hyc-common-markdown__ref_card-foot__source_txt"
)

REFERENCE_TITLE_SELECTOR = (
    ".hyc-common-markdown__ref_card-title"
)

REFERENCE_DESC_SELECTOR = (
    ".hyc-common-markdown__ref_card-desc"
)

REFERENCE_CLOSE_SELECTOR = (
    ".agent-dialogue-references__close"
)

QUESTION_ITEM_SELECTOR = (
    ".chat-content-item-user"
)

QUESTION_TEXT_SELECTOR = (
    ".chat-content-item-user "
    ".user-content__text"
)

ASSISTANT_ITEM_SELECTOR = (
    ".chat-content-item-assistant"
)

THINKING_CONTAINER_SELECTOR = (
    ".thinking-container"
)

ASSISTANT_ACTIONS_SELECTOR = (
    ".segment-assistant-actions"
)

CITATION_SELECTOR = (
    "a.pua-ref-cite-tag[href]"
)


MODEL_OPTION_SELECTOR = (
    'button.model-item'
    '[role="menuitemradio"]'
)

MODEL_NAME_SELECTOR = (
    ".model-name .name"
)

EFFORT_ENTRY_SELECTOR = (
    "button.effort-item"
)

EFFORT_OPTION_SELECTOR = (
    'button.effort-option'
    '[role="menuitemradio"]'
)

EFFORT_VALUE_SELECTOR = (
    ".effort-value"
)

CURRENT_EFFORT_SELECTOR = (
    ".current-effort"
)
EFFORT_NAME_SELECTOR = (
    ".effort-name"
)