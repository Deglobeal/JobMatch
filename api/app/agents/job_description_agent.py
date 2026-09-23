"""Structured contract for JobMatch Agent 1: Job Description Analyst."""

from pydantic import BaseModel, Field


class JobRequirement(BaseModel):
    """A single requirement extracted from a job description."""

    text: str
    category: str
    importance: str
    explicit: bool = True


class JobDescriptionAnalysis(BaseModel):
    """Structured analysis produced by Agent 1."""

    job_title: str | None = None

    responsibilities: list[str] = Field(default_factory=list)

    required_qualifications: list[JobRequirement] = Field(
        default_factory=list
    )

    preferred_qualifications: list[JobRequirement] = Field(
        default_factory=list
    )

    skills: list[str] = Field(default_factory=list)

    experience_requirements: list[str] = Field(
        default_factory=list
    )

    education_requirements: list[str] = Field(
        default_factory=list
    )

    certification_requirements: list[str] = Field(
        default_factory=list
    )

    keywords: list[str] = Field(default_factory=list)

    industry_context: list[str] = Field(default_factory=list)

    ambiguous_requirements: list[str] = Field(
        default_factory=list
    )
