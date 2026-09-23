"""Regression tests for JobMatch Agent 2: CV Analyst."""

import asyncio

from app.agents.cv_agent import CVAnalysis
from app.agents.cv_analyzer import CVAnalyzer


class FakeGeminiProvider:
    """Return a controlled structured CV analysis without calling Gemini."""

    def __init__(self, result: CVAnalysis):
        self.result = result
        self.calls = []

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model,
    ):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_model": response_model,
            }
        )
        return self.result


def test_cv_analyzer_preserves_structured_education_and_certifications():
    """Agent 2 should keep education and certifications as separate fields."""

    expected = CVAnalysis(
        candidate_name="UGWU GERARD O",
        likely_roles=["Junior Software Developer"],
        seniority="Junior",
        education=[
            "ALX Software Engineering Programmes — DevOps • Backend Engineering • Professional Foundations"
        ],
        certifications=[],
    )

    provider = FakeGeminiProvider(expected)
    analyzer = CVAnalyzer(provider=provider)

    result = asyncio.run(
        analyzer.analyze(
            cv_text="""
            UGWU GERARD O
            JUNIOR SOFTWARE DEVELOPER

            EDUCATION
            ALX Software Engineering Programmes
            DevOps • Backend Engineering • Professional Foundations
            """
        )
    )

    assert result.education == expected.education
    assert result.certifications == []
    assert "ALX Software Engineering Programmes" in result.education[0]
    assert "ALX Alumni" not in result.certifications


def test_cv_analyzer_rejects_empty_cv():
    """Agent 2 should reject empty CV content before calling the provider."""

    provider = FakeGeminiProvider(CVAnalysis())
    analyzer = CVAnalyzer(provider=provider)

    try:
        asyncio.run(analyzer.analyze(cv_text="   "))
    except ValueError as exc:
        assert str(exc) == "CV content is required."
    else:
        raise AssertionError("Expected ValueError for empty CV")

    assert provider.calls == []


def test_cv_analyzer_preserves_experience_dates_and_location():
    """Agent 2 should preserve explicitly supplied experience metadata."""

    expected = CVAnalysis(
        experiences=[
            {
                "organization": "Sokosq",
                "role": "Backend Development",
                "location": "Lagos, Nigeria",
                "start_date": "Jan 2026",
                "end_date": "June 2026",
                "responsibilities": ["Built backend services."],
                "achievements": [],
            }
        ]
    )

    provider = FakeGeminiProvider(expected)
    analyzer = CVAnalyzer(provider=provider)

    result = asyncio.run(
        analyzer.analyze(
            cv_text="""
            EXPERIENCE

            Backend Development
            Sokosq
            Lagos, Nigeria
            Jan 2026 - June 2026

            Built backend services.
            """
        )
    )

    experience = result.experiences[0]

    assert experience.organization == "Sokosq"
    assert experience.role == "Backend Development"
    assert experience.location == "Lagos, Nigeria"
    assert experience.start_date == "Jan 2026"
    assert experience.end_date == "June 2026"


def test_cv_analyzer_preserves_project_link_labels_and_association():
    """Agent 2 should preserve explicit project link labels and ownership."""

    expected = CVAnalysis(
        projects=[
            {
                "name": "BuildOS",
                "description": "Construction materials marketplace.",
                "technologies": ["Python", "FastAPI"],
                "bullets": ["Built backend services."],
                "links": [
                    {
                        "label": "Live Demo",
                        "url": "https://buildoshub.vercel.app",
                    },
                    {
                        "label": "API Docs",
                        "url": "https://example.com/docs",
                    },
                ],
            }
        ]
    )

    provider = FakeGeminiProvider(expected)
    analyzer = CVAnalyzer(provider=provider)

    result = asyncio.run(
        analyzer.analyze(
            cv_text="""
            PROJECTS

            BuildOS
            Construction materials marketplace.
            Live Demo ---- https://buildoshub.vercel.app
            API Docs: https://example.com/docs
            """
        )
    )

    project = result.projects[0]

    assert project.name == "BuildOS"
    assert [
        (link.label, link.url)
        for link in project.links
    ] == [
        ("Live Demo", "https://buildoshub.vercel.app"),
        ("API Docs", "https://example.com/docs"),
    ]


def test_cv_analyzer_does_not_invent_ambiguous_project_link_ownership():
    """Agent 2 must not assign an ambiguous link to the wrong project."""

    expected = CVAnalysis(
        projects=[
            {
                "name": "Project Alpha",
                "description": "A web application.",
                "links": [],
            },
            {
                "name": "Project Beta",
                "description": "An API service.",
                "links": [],
            },
        ],
        evidence_notes=[
            "A project link was present in the extracted CV text, but its project ownership could not be established reliably."
        ],
    )

    provider = FakeGeminiProvider(expected)
    analyzer = CVAnalyzer(provider=provider)

    result = asyncio.run(
        analyzer.analyze(
            cv_text="""
            PROJECTS

            Project Alpha
            A web application.

            Project Beta
            An API service.

            Demo --- https://example.com/demo
            """
        )
    )

    assert all(not project.links for project in result.projects)
    assert any(
        "ownership" in note.lower()
        for note in result.evidence_notes
    )
