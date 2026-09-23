"""Structured CV document models for JobMatch."""

from pydantic import BaseModel, Field


class CVLink(BaseModel):
    """A clickable link found in a CV."""

    label: str
    url: str


class CVPersonalDetails(BaseModel):
    """Professional identity and contact information."""

    name: str | None = None
    headline: str | None = None
    location: str | None = None
    phone: str | None = None
    email: str | None = None
    links: list[CVLink] = Field(default_factory=list)


class CVExperienceDocument(BaseModel):
    """A professional experience entry."""

    organization: str | None = None
    role: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    links: list[CVLink] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)


class CVProjectDocument(BaseModel):
    """A project entry."""

    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    links: list[CVLink] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)


class CVDocument(BaseModel):
    """Structured representation of a CV."""

    personal: CVPersonalDetails = Field(
        default_factory=CVPersonalDetails
    )

    summary: str | None = None

    experience: list[CVExperienceDocument] = Field(
        default_factory=list
    )

    projects: list[CVProjectDocument] = Field(
        default_factory=list
    )

    education: list[str] = Field(default_factory=list)

    certifications: list[str] = Field(default_factory=list)

    skills: list[str] = Field(default_factory=list)

    source_text: str = ""
