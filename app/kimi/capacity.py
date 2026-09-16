from __future__ import annotations

CAPACITY_LIMIT_MARKERS = (
    "和Kimi",
    "订阅会员可进入优先队列",
)


def _normalize(text: str | None) -> str:
    if not text:
        return ""

    return "".join(
        str(text).split()
    )


def is_service_capacity_limited(
        text: str | None,
) -> bool:
    normalized = _normalize(text)

    if not normalized:
        return False

    return all(
        _normalize(marker) in normalized
        for marker in CAPACITY_LIMIT_MARKERS
    )
