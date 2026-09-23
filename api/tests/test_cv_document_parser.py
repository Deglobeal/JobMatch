"""Tests for deterministic structured CV document parsing."""

from app.services.cv_document_parser import CVDocumentParser


def test_parses_generic_cv_header():
    """A generic CV header should produce structured personal details."""

    cv_text = """Jane Doe
Senior Backend Developer
Accra, Ghana | +233-555-123-456 | jane@example.com
https://github.com/janedoe | Portfolio: https://janedoe.dev | LinkedIn: https://linkedin.com/in/janedoe
SUMMARY
Backend developer with Python experience.
"""

    document = CVDocumentParser().parse(cv_text)

    assert document.personal.name == "Jane Doe"
    assert document.personal.headline == "Senior Backend Developer"
    assert document.personal.location == "Accra, Ghana"
    assert document.personal.phone == "+233-555-123-456"
    assert document.personal.email == "jane@example.com"


def test_extracts_generic_header_links():
    """Header URLs should be preserved as structured links."""

    cv_text = """John Smith
Software Engineer
Lagos, Nigeria | +234-800-111-2222 | john@example.com
https://github.com/johnsmith | Portfolio: https://johnsmith.dev | LinkedIn: https://linkedin.com/in/johnsmith
"""

    document = CVDocumentParser().parse(cv_text)

    assert {
        link.label: link.url
        for link in document.personal.links
    } == {
        "GitHub": "https://github.com/johnsmith",
        "Portfolio": "https://johnsmith.dev",
        "LinkedIn": "https://linkedin.com/in/johnsmith",
    }


def test_preserves_explicit_link_label():
    """An explicit label next to a URL should be preserved."""

    cv_text = """Alex Brown
Backend Developer
Kumasi, Ghana | +233-555-000-1111 | alex@example.com
Live Demo: https://example.com/demo
"""

    document = CVDocumentParser().parse(cv_text)

    assert len(document.personal.links) == 1
    assert document.personal.links[0].label == "Live Demo"
    assert document.personal.links[0].url == "https://example.com/demo"


def test_does_not_hard_code_specific_candidate_values():
    """The parser should work with another candidate's details."""

    cv_text = """Michael Okafor
Frontend Developer
Abuja, Nigeria | +234-801-222-3333 | michael@example.com
https://github.com/michaelokafor
"""

    document = CVDocumentParser().parse(cv_text)

    assert document.personal.name == "Michael Okafor"
    assert document.personal.headline == "Frontend Developer"
    assert document.personal.location == "Abuja, Nigeria"
    assert document.personal.email == "michael@example.com"
    assert document.personal.links[0].url == "https://github.com/michaelokafor"


def test_rejects_empty_cv_text():
    """Empty CV content should raise a clear error."""

    import pytest

    with pytest.raises(ValueError, match="CV content is required"):
        CVDocumentParser().parse("")


def test_extracts_project_link_labels_without_hard_coding():
    """Project links should preserve explicit labels from arbitrary CV text."""

    text = """Jane Doe
Backend Developer
Accra, Ghana | jane@example.com

PROJECTS
Alpha Platform
Python • FastAPI • Remote Demo ---- https://alpha.example.com

Beta API
Python • REST APIs • API Docs: https://beta.example.com/docs

Gamma App
React • TypeScript • Demo---https://gamma.example.com

Delta Portfolio
Django • Demo link ---- https://delta.example.com
"""

    parser = CVDocumentParser()
    links = parser._extract_links(text)

    assert [
        (link.label, link.url)
        for link in links
    ] == [
        ("Remote Demo", "https://alpha.example.com"),
        ("API Docs", "https://beta.example.com/docs"),
        ("Demo", "https://gamma.example.com"),
        ("Demo link", "https://delta.example.com"),
    ]


def test_personal_links_do_not_include_project_links():
    """Personal links should come from the CV header, not project sections."""

    cv_text = """Jane Doe
Backend Developer
Lagos, Nigeria | +234-800-111-2222 | jane@example.com
https://github.com/janedoe | Portfolio: https://janedoe.dev | LinkedIn: https://linkedin.com/in/janedoe

PROJECTS

BuildOS
Live Demo: https://buildoshub.vercel.app

Authentication Service
API Docs: https://example.com/docs
"""

    document = CVDocumentParser().parse(cv_text)

    assert [
        (link.label, link.url)
        for link in document.personal.links
    ] == [
        ("GitHub", "https://github.com/janedoe"),
        ("Portfolio", "https://janedoe.dev"),
        ("LinkedIn", "https://linkedin.com/in/janedoe"),
    ]
