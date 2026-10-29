import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from . import llm


ALLOWED_FLAGS = {
    "customer_data_shared",
    "confidential_data_shared",
    "unreviewed_output",
    "policy_unaware",
}


class ScoringError(ValueError):
    pass


class ScoringResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int = Field(ge=1, le=5)
    reason: str = Field(min_length=1)
    flags: list[str] = Field(default_factory=list)


def score_open_answer(question_text: str, answer: str) -> dict:
    raw = llm.score_answer(question_text, answer)
    cleaned = raw.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned[3:-3].strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        data = ScoringResult.model_validate_json(cleaned)
    except (ValidationError, json.JSONDecodeError) as exc:
        raise ScoringError("The AI scoring service returned an invalid result") from exc
    if any(flag not in ALLOWED_FLAGS for flag in data.flags):
        raise ScoringError("The AI scoring service returned an unknown risk flag")
    return data.model_dump()
