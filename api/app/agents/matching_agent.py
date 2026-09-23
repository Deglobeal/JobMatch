"""Structured contract for JobMatch Agent 3: Matching & Improvement Agent."""

from pydantic import BaseModel, Field


class MatchEvidence(BaseModel):
    """Evidence supporting a match, partial match, or gap."""

    requirement: str
    evidence: str
    status: str


class CVImprovement(BaseModel):
    """A suggested CV improvement grounded in existing evidence."""

    section: str
    current_evidence: str
    suggested_change: str
    reason: str


class MatchingAnalysis(BaseModel):
    """Structured final analysis produced by Agent 3."""

    match_percentage: int = Field(
        ge=0,
        le=100,
    )

    overall_assessment: str

    strong_matches: list[MatchEvidence] = Field(
        default_factory=list
    )

    partial_matches: list[MatchEvidence] = Field(
        default_factory=list
    )

    missing_or_unclear: list[MatchEvidence] = Field(
        default_factory=list
    )

    transferable_experience: list[str] = Field(
        default_factory=list
    )

    keywords_to_consider: list[str] = Field(
        default_factory=list
    )

    cv_improvements: list[CVImprovement] = Field(
        default_factory=list
    )

    suggested_rewrites: list[str] = Field(
        default_factory=list
    )

    should_tailor_cv: bool

    tailoring_priority: list[str] = Field(
        default_factory=list
    )

    truth_warnings: list[str] = Field(
        default_factory=list
    )
