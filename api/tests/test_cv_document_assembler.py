"""Tests for assembling a structured CV document."""

from app.agents.cv_agent import (
    CVAnalysis,
    CVExperience,
    CVProject,
)
from app.services.cv_document import CVDocument, CVLink, CVPersonalDetails


def test_cv_document_accepts_structured_sections():
    """CVDocument should represent personal details, experience, and projects."""

    document = CVDocument(
        personal=CVPersonalDetails(
            name="Jane Doe",
            headline="Backend Developer",
            location="Accra, Ghana",
            phone="+233-555-123-456",
            email="jane@example.com",
            links=[
                CVLink(
                    label="GitHub",
                    url="https://github.com/janedoe",
                )
            ],
        ),
        summary="Backend developer.",
        education=["BSc Computer Science"],
        certifications=["AWS Certified Cloud Practitioner"],
        skills=["Python", "FastAPI"],
        source_text="Jane Doe\nBackend Developer",
    )

    assert document.personal.name == "Jane Doe"
    assert document.personal.links[0].label == "GitHub"
    assert document.skills == ["Python", "FastAPI"]


def test_agent2_experience_contract_contains_document_fields():
    """Agent 2 experience data should contain factual document fields."""

    experience = CVExperience(
        organization="Example Company",
        role="Backend Developer",
        location="Lagos, Nigeria",
        start_date="Jan 2025",
        end_date="Jun 2025",
        responsibilities=["Built APIs."],
        achievements=["Fixed production bugs."],
    )

    assert experience.organization == "Example Company"
    assert experience.location == "Lagos, Nigeria"
    assert experience.start_date == "Jan 2025"
    assert experience.end_date == "Jun 2025"


def test_agent2_project_contract_contains_document_fields():
    """Agent 2 project data should contain structured project fields."""

    project = CVProject(
        name="Example Project",
        description="Example application.",
        technologies=["Python", "FastAPI"],
        bullets=["Built an API."],
        links=[
            {
                "label": "Live Demo",
                "url": "https://example.com",
            }
        ],
    )

    assert project.name == "Example Project"
    assert project.technologies == ["Python", "FastAPI"]
    assert project.links[0].label == "Live Demo"


def test_assembler_preserves_project_link_associations():
    """Project links must remain associated with their source project."""

    from app.services.cv_document_assembler import CVDocumentAssembler

    cv_text = """Project Alpha
Built a web application.
Live Demo: https://alpha.example.com

Project Beta
Built an API service.
API Docs: https://beta.example.com/docs
"""

    analysis = CVAnalysis(
        projects=[
            CVProject(
                name="Project Alpha",
                description="Built a web application.",
                links=[
                    {
                        "label": "Live Demo",
                        "url": "https://alpha.example.com",
                    }
                ],
            ),
            CVProject(
                name="Project Beta",
                description="Built an API service.",
                links=[
                    {
                        "label": "API Docs",
                        "url": "https://beta.example.com/docs",
                    }
                ],
            ),
        ],
    )

    document = CVDocumentAssembler().assemble(
        cv_text=cv_text,
        analysis=analysis,
    )

    projects = {
        project.name: project
        for project in document.projects
    }

    assert [
        link.model_dump()
        for link in projects["Project Alpha"].links
    ] == [
        {
            "label": "Live Demo",
            "url": "https://alpha.example.com",
        }
    ]

    assert [
        link.model_dump()
        for link in projects["Project Beta"].links
    ] == [
        {
            "label": "API Docs",
            "url": "https://beta.example.com/docs",
        }
    ]
