from app.kimi.geo_contract import (
    build_answer_id,
    build_question_id,
    build_task_id,
    resolve_product,
    to_geo_mode,
)
from app.kimi.types import KimiMode


def test_geo_mode_mapping():
    assert (
        to_geo_mode(KimiMode.STANDARD)
        == "quick"
    )

    assert (
        to_geo_mode(KimiMode.ADVANCED)
        == "expert"
    )


def test_resolve_hongmao():
    assert resolve_product(
        "鸿茅药酒"
    ) == (
        "hongmao_yaojiu",
        "鸿茅药酒",
    )


def test_resolve_tianyishou():
    assert resolve_product(
        "天益寿气血固本"
    ) == (
        "tianyishou_qixueguben",
        "天益寿气血固本",
    )


def test_question_id_is_stable():
    first = build_question_id(
        "001",
        "测试问题",
    )

    second = build_question_id(
        "001",
        "测试问题",
    )

    assert first == second
    assert first.startswith(
        "kimiq_001_"
    )


def test_task_and_answer_id_prefix():
    question_id = build_question_id(
        "001",
        "测试问题",
    )

    task_id = build_task_id(
        "batch_001",
        question_id,
        "quick",
    )

    answer_id = build_answer_id(
        "batch_001",
        task_id,
    )

    assert task_id.startswith(
        "kimi_t_"
    )

    assert answer_id.startswith(
        "kimi_a_"
    )