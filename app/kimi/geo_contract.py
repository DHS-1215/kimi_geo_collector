from __future__ import annotations

import hashlib

from app.kimi.types import KimiMode

GEO_SCHEMA_VERSION = "geo_package_v1"
GEO_BATCH_VERSION = "geo_batch_v1"

KIMI_PLATFORM_CODE = "kimi"
KIMI_PLATFORM_NAME = "KIMI"

DEFAULT_PRODUCT_ID = "hongmao_yaojiu"
DEFAULT_PRODUCT_NAME = "鸿茅药酒"

COLLECTOR_VERSION = "0.1.0"

PRODUCT_REGISTRY = {
    "鸿茅药酒": {
        "product_id": "hongmao_yaojiu",
        "product_name": "鸿茅药酒",
    },
    "天益寿气血固本": {
        "product_id": "tianyishou_qixueguben",
        "product_name": "天益寿气血固本",
    },
}


def resolve_product(
        product_name: str,
) -> tuple[str, str]:

    normalized_name = (
        product_name.strip()
    )

    product = (
        PRODUCT_REGISTRY.get(
            normalized_name
        )
    )

    if product is None:
        raise ValueError(
            "未知采集产品："
            f"{product_name}"
        )

    return (
        product["product_id"],
        product["product_name"],
    )


def to_geo_mode(
        mode: KimiMode,
) -> str:
    """
    将 KIMI 思考强度映射到 GEO v1
    的统一采集模式。

    GEO v1 当前保持：
    - quick
    - expert

    KIMI“极致”虽然客户端支持，
    但暂不纳入 GEO v1 标准批次，
    避免与“进阶”共同映射为 expert
    后产生任务身份冲突。
    """

    if mode == KimiMode.STANDARD:
        return "quick"

    if mode == KimiMode.ADVANCED:
        return "expert"

    if mode == KimiMode.EXTREME:
        raise ValueError(
            "KIMI“极致”暂不纳入 "
            "GEO v1 标准模式"
        )

    raise ValueError(
        f"未知KIMI模式：{mode}"
    )


def normalize_question_text(
        text: str,
) -> str:
    return (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .strip()
    )


def _stable_hash(
        *parts: object,
        length: int = 24,
) -> str:
    payload = "\n".join(
        str(part)
        for part in parts
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()[:length]


def build_question_id(
        csv_id: str,
        question: str,
) -> str:
    normalized_question = (
        normalize_question_text(
            question
        )
    )

    question_hash = _stable_hash(
        normalized_question,
        length=12,
    )

    return (
        f"kimiq_{csv_id.strip()}_"
        f"{question_hash}"
    )


def build_task_id(
        batch_id: str,
        question_id: str,
        mode_code: str,
) -> str:
    digest = _stable_hash(
        KIMI_PLATFORM_CODE,
        batch_id,
        question_id,
        mode_code,
    )

    return f"kimi_t_{digest}"


def build_answer_id(
        batch_id: str,
        task_id: str,
) -> str:
    digest = _stable_hash(
        KIMI_PLATFORM_CODE,
        batch_id,
        task_id,
    )

    return f"kimi_a_{digest}"


def build_occurrence_id(
        batch_id: str,
        answer_id: str,
        source_order: int,
        source_url_raw: str,
) -> str:
    digest = _stable_hash(
        KIMI_PLATFORM_CODE,
        batch_id,
        answer_id,
        source_order,
        source_url_raw.strip(),
    )

    return f"kimi_s_{digest}"
