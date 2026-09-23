"""Structured contract for the JobMatch CV Improvement Agent."""

from pydantic import BaseModel, Field


class CVImprovementItem(BaseModel):
    """A safe, evidence-grounded improvement to the editable CV."""

    section: str
    field: str
    reason: str
    current_content: str
    proposed_content: str
    evidence_used: list[str] = Field(default_factory=list)
    expected_match_impact: str
    safe_to_apply: bool


class CVImprovementPlan(BaseModel):
    """Structured plan for improving CV alignment with a target job."""

    current_match: int = Field(
        ge=0,
        le=100,
    )

    potential_match: int = Field(
        ge=0,
        le=100,
    )

    overall_assessment: str

    improvements: list[CVImprovementItem] = Field(
        default_factory=list
    )

    priority_order: list[str] = Field(
        default_factory=list
    )

    unsupported_requirements: list[str] = Field(
        default_factory=list
    )

    truth_warnings: list[str] = Field(
        default_factory=list
    )

    safe_to_apply_all: bool
