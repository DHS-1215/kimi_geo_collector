from dataclasses import dataclass, field

from app.kimi.source import KimiSource

from datetime import datetime, timezone


@dataclass
class KimiCollectionResult:
    question: str

    answer: str

    model: str

    mode: str

    conversation_url: str

    sources: list[KimiSource] = field(
        default_factory=list
    )

    status: str = "success"

    error: str = ""

    task_id: str = ""

    question_id: str = ""

    mode_code: str = ""

    batch_id: str = ""

    product: str = ""

    platform: str = "kimi"

    acquisition_status: str = "success"

    validation_status: str = "NOT_APPLICABLE"

    is_complete: bool = True

    source_collection_status: str = "success"

    source_count_raw: int = 0

    source_error: str = ""

    collected_at: str = ""


def utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()
