from __future__ import annotations


# 可以通过冷却后再次尝试的普通风控
RISK_CONTROL_MARKERS = (
    "访问过于频繁",
    "操作过于频繁",
    "请求过于频繁",
    "请勿频繁操作",
    "检测到异常访问",
    "当前访问存在异常",
    "当前账号存在异常",
    "账号存在异常",
    "请完成安全验证",
    "完成安全验证后继续",
)


def _normalize(
        text: str | None,
) -> str:
    if not text:
        return ""

    return "".join(
        str(text).split()
    )


def find_risk_control_marker(
        text: str | None,
) -> str | None:
    normalized = _normalize(
        text
    )

    if not normalized:
        return None

    for marker in RISK_CONTROL_MARKERS:
        normalized_marker = _normalize(
            marker
        )

        if (
            normalized_marker
            in normalized
        ):
            return marker

    return None