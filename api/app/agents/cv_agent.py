"""Structured contract for JobMatch Agent 2: CV Analyst."""

from pydantic import BaseModel, Field


class CVLink(BaseModel):
    """A link associated with a CV experience or project."""

    label: str
    url: str


class CVExperience(BaseModel):
    """A role or experience extracted from a CV."""

    role: str | None = None
    organization: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    industry: str | None = None
    links: list[CVLink] = Field(default_factory=list)


class CVProject(BaseModel):
    """A project extracted from a CV."""

    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    links: list[CVLink] = Field(default_factory=list)


class CVAnalysis(BaseModel):
    """Structured analysis produced by Agent 2."""

    candidate_name: str | None = None

    professional_summary: str | None = None

    likely_roles: list[str] = Field(default_factory=list)

    seniority: str | None = None

    skills: list[str] = Field(default_factory=list)

    experiences: list[CVExperience] = Field(
        default_factory=list
    )

    projects: list[CVProject] = Field(
        default_factory=list
    )

    education: list[str] = Field(default_factory=list)

    certifications: list[str] = Field(default_factory=list)

    tools_and_software: list[str] = Field(
        default_factory=list
    )

    industries: list[str] = Field(default_factory=list)

    transferable_skills: list[str] = Field(
        default_factory=list
    )

    achievements: list[str] = Field(
        default_factory=list
    )

    evidence_notes: list[str] = Field(
        default_factory=list
    )
