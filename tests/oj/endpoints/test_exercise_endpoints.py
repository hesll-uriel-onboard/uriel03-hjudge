from json import JSONDecoder
from typing import List, Tuple

import pytest
from litestar.app import Litestar
from litestar.testing import TestClient

from hjudge.oj.models.judges.factory import JudgeFactory

valid_problems = [
    {"judge": "CODEFORCES", "code": "566A", "title": "Matching Names"},
    {
        "judge": "CODEFORCES",
        "code": "2205G",
        "title": "Simons and Diophantus Equation",
    },
    {
        "judge": "CODEFORCES",
        "code": "2201F1",
        "title": "Monotone Monochrome Matrices (Medium Version)",
    },
]
problem_with_invalid_judge = {
    "judge": "jfdksjfsdl",
    "code": "566A",
    "title": "Matching Names",
}
problems_with_invalid_code = {
    "judge": "CODEFORCES",
    "code": "sfds",
    "title": "Matching Names",
}
non_existed_problem = {
    "judge": "CODEFORCES",
    "code": "566X",
    "title": "Matching Names",
}

one_valid_one_invalid_same_contest = [
    ({"judge": "CODEFORCES", "code": "566A", "title": "Matching Names"}, 200),
    ({"judge": "CODEFORCES", "code": "566X", "title": "Matching Names"}, 404),
]
two_valid_same_contest = [
    ({"judge": "CODEFORCES", "code": "2185G", "title": "Mixing MEXes"}, 200),
    (
        {"judge": "CODEFORCES", "code": "2185D", "title": "OutOfMemoryError"},
        200,
    ),
]


# scenario:
# 1. add one valid problem
# 2. add one invalid problem
# 3. add two valid problems of different contest
# 4. add two valid problems of same contest
# 5. add one valid problem and one invalid problem of the same contest
@pytest.mark.parametrize(
    "exercises",
    [
        # 1
        [(valid_problems[0], 200), (valid_problems[2], 200)],
        # 2
        [
            (problem_with_invalid_judge, 400),
            (problems_with_invalid_code, 404),
            (non_existed_problem, 404),
        ],
        # 3
        [(obj, 200) for obj in valid_problems],
        # 4
        two_valid_same_contest,
        # 5
        one_valid_one_invalid_same_contest,
    ],
)
def test_chaining_check_exercise_existed(
    mocked_app: Litestar, mock_judge_factory: JudgeFactory, exercises: List[Tuple[dict, int]]
):
    for exercise, status_code in exercises:
        with TestClient(app=mocked_app) as client:
            client.get(
                f"/api/exercises?judge={exercise["judge"]}&code={exercise["code"]}"
            )
            response = client.get(
                f"/api/exercises?judge={exercise["judge"]}&code={exercise["code"]}"
            )
            assert response is not None

        assert response.status_code == status_code
        if status_code == 200:
            result = JSONDecoder().decode(response.content.decode())
            assert result["judge"] == exercise["judge"]
            assert result["code"] == exercise["code"]
            assert result["title"] == exercise["title"]
            assert result["url"] == mock_judge_factory.create_from(
                exercise["judge"]
            ).get_exercise_url(exercise["code"])


# # def test_duplicate_exercise_import()
