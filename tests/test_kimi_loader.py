from pathlib import Path

from app.kimi.loader import load_questions


def test_load_questions_utf8(tmp_path: Path):
    csv_path = (
            tmp_path
            / "questions.csv"
    )

    csv_path.write_text(
        "id,question\n"
        "001,测试问题一\n"
        "002,测试问题二\n",
        encoding="utf-8",
    )

    questions = load_questions(
        str(csv_path)
    )

    assert len(questions) == 2

    assert questions[0].question == (
        "测试问题一"
    )

    assert questions[1].question == (
        "测试问题二"
    )


def test_load_questions_utf8_bom(
        tmp_path: Path,
):
    csv_path = (
            tmp_path
            / "questions_bom.csv"
    )

    csv_path.write_text(
        "id,question\n"
        "001,天益寿测试问题\n",
        encoding="utf-8-sig",
    )

    questions = load_questions(
        str(csv_path)
    )

    assert len(questions) == 1

    assert (
            questions[0].question
            == "天益寿测试问题"
    )

    assert (
        questions[0].question_id
        .startswith("kimiq_001_")
    )
