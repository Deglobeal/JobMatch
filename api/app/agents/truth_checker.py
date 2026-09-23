"""JobMatch Truth Checker: validates AI-generated CV suggestions."""

from pydantic import BaseModel, Field


class TruthCheckItem(BaseModel):
    """Validation result for one proposed CV change."""

    suggestion: str
    status: str
    evidence: str | None = None
    reason: str


class TruthCheckResult(BaseModel):
    """Structured result from the Truth Checker."""

    approved_suggestions: list[TruthCheckItem] = Field(
        default_factory=list
    )

    rejected_suggestions: list[TruthCheckItem] = Field(
        default_factory=list
    )

    warnings: list[str] = Field(
        default_factory=list
    )

    all_suggestions_safe: bool
