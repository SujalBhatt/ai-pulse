from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..auth import current_membership
from ..services.questions import questions_for
from ..services.scoring import ScoringError, score_open_answer

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


class AnswerIn(BaseModel):
    question_id: str
    answer: str


class SubmitIn(BaseModel):
    answers: list[AnswerIn]


@router.get("/questions")
def get_questions(m: models.Membership = Depends(current_membership)):
    qs = questions_for(m.job_role, m.seniority)
    # don't leak scoring points to the client
    return [
        {k: v for k, v in q.items() if k != "points"} | (
            {"options": [o["text"] for o in q["options"]]} if q["type"] == "mcq" else {}
        )
        for q in qs
    ]


@router.post("/submit")
def submit(body: SubmitIn, m: models.Membership = Depends(current_membership), db: Session = Depends(get_db)):
    bank = {q["id"]: q for q in questions_for(m.job_role, m.seniority)}
    question_ids = [a.question_id for a in body.answers]
    if not question_ids or len(question_ids) != len(set(question_ids)):
        raise HTTPException(400, "Each question must be answered exactly once")
    expected_ids = set(bank)
    if set(question_ids) != expected_ids:
        raise HTTPException(400, "Complete all diagnostic questions before submitting")

    responses = []
    for a in body.answers:
        q = bank.get(a.question_id)
        if not q:
            raise HTTPException(400, f"Unknown question {a.question_id}")
        answer = a.answer.strip()
        if not answer:
            raise HTTPException(400, f"Answer required for {q['id']}")
        resp = models.Response(membership_id=m.id, question_id=q["id"], answer=answer)
        if q["type"] == "mcq":
            option = next((o for o in q["options"] if o["text"] == answer), None)
            if option is None:
                raise HTTPException(400, f"Invalid option for {q['id']}")
            resp.score = option["points"]
        else:
            try:
                result = score_open_answer(q["text"], answer)
            except ScoringError as exc:
                db.rollback()
                raise HTTPException(502, str(exc)) from exc
            resp.score = result["score"]
            resp.reason = result["reason"]
            resp.flags = result["flags"]
        responses.append(resp)

    db.query(models.Response).filter_by(membership_id=m.id).delete()
    db.add_all(responses)
    db.commit()
    return {"saved": len(responses)}
