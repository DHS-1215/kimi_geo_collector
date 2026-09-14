import csv
from app.kimi.geo_contract import build_question_id

from app.kimi.runner import KimiQuestion


def load_questions(
        path: str,
) -> list[KimiQuestion]:
    questions = []

    with open(
            path,
            "r",
            encoding="utf-8",
    ) as file:
        reader = csv.DictReader(
            file
        )

        for row in reader:
            csv_id = row["id"].strip()
            question = row["question"].strip()

            question_id = build_question_id(
                csv_id=csv_id,
                question=question,
            )

            questions.append(
                KimiQuestion(
                    question_id=question_id,
                    question=question,
                )
            )

    return questions
