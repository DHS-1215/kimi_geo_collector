from enum import StrEnum
from dataclasses import dataclass, field


class KimiMode(StrEnum):
    QUICK = "快速回答"
    THINKING = "深度思考"
    EXPERT = "专家模式"


class KimiModel(StrEnum):
    HY3 = "Hy3"
    DEEPSEEK = "DeepSeek"
    HY4_PREVIEW = "Hy4 preview"


MODEL_MODE_COMPATIBILITY = {
    KimiModel.HY3: {
        KimiMode.QUICK,
        KimiMode.THINKING,
        KimiMode.EXPERT,
    },
    KimiModel.DEEPSEEK: {
        KimiMode.QUICK,
        KimiMode.THINKING,
    },
    KimiModel.HY4_PREVIEW: {
        KimiMode.EXPERT,
    },
}


@dataclass
class KimiSource:
    title: str = ""
    url: str = ""
    domain: str = ""


@dataclass
class KimiResult:
    question: str

    answer: str

    model: str

    mode: str

    url: str

    sources: list[KimiSource] = field(default_factory=list)

    status: str = "success"

    error: str = ""
