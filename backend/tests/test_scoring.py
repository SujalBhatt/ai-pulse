import pytest

from app.services import llm
from app.services.scoring import ScoringError, score_open_answer


@pytest.mark.parametrize(
    "raw",
    [
        '{"score": 7, "reason": "Too high", "flags": []}',
        '{"score": "four", "reason": "Not numeric", "flags": []}',
        '{"score": 3, "reason": "Unknown flag", "flags": ["made_up"]}',
        '{"score": 3, "flags": []}',
    ],
)
def test_invalid_model_output_is_rejected(monkeypatch, raw):
    monkeypatch.setattr(llm, "score_answer", lambda question, answer: raw)

    with pytest.raises(ScoringError):
        score_open_answer("Question", "Answer")


def test_fenced_valid_model_output_is_accepted(monkeypatch):
    monkeypatch.setattr(
        llm,
        "score_answer",
        lambda question, answer: '```json\n{"score": 4, "reason": "Reviewed", "flags": []}\n```',
    )

    assert score_open_answer("Question", "Answer") == {
        "score": 4,
        "reason": "Reviewed",
        "flags": [],
    }
