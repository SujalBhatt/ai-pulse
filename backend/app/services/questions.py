import json
import os

_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "questions.json")
SENIORITY_LEVELS = {"junior": 1, "mid": 2, "senior": 3, "lead": 4}


def load_questions():
    with open(_PATH) as f:
        return json.load(f)


def questions_for(job_role: str, seniority: str):
    """Common questions for everyone + questions for this job role, filtered by seniority."""
    result = []
    for q in load_questions():
        if q["roles"] != ["all"] and job_role not in q["roles"]:
            continue
        if SENIORITY_LEVELS.get(seniority, 0) < SENIORITY_LEVELS.get(q.get("min_seniority", "junior"), 0):
            continue
        result.append(q)
    return result
