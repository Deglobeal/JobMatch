"""Tests for CV profile extraction."""

from app.services.cv_profile import CVProfileExtractor


def test_extracts_generic_cv_profile():
    """A normal CV should produce a searchable profile."""

    cv_text = """
    JANE DOE
    jane@example.com
    https://linkedin.com/in/janedoe

    PROFESSIONAL SUMMARY
    Customer service specialist with five years of experience helping
    customers, resolving issues, and improving customer satisfaction.

    EXPERIENCE
    Customer Service Specialist
    Example Company
    2022 - 2026
    Handled customer inquiries and resolved support issues.

    SKILLS
    Customer Service, Communication, CRM, Problem Solving

    EDUCATION
    Bachelor of Business Administration
    """

    profile = CVProfileExtractor().extract(cv_text)

    assert profile["target_role"] == "Customer service specialist"
    assert "customer service" in profile["summary"].lower()
    assert "Customer Service" in profile["skills"]
    assert "Communication" in profile["skills"]
    assert profile["experience"] is not None
    assert "Customer Service Specialist" in profile["experience"]
    assert "Customer service specialist" in profile["search_query"]


def test_extracts_profile_from_realistic_multisection_cv():
    """A CV with common heading variants should be parsed correctly."""

    cv_text = """
    JOHN SMITH
    john@example.com | Lagos, Nigeria

    PYTHON / BACKEND DEVELOPER

    PROFESSIONAL PROFILE
    Python backend developer experienced in building APIs and database-backed
    applications. Strong experience with FastAPI, Django, and PostgreSQL.

    WORK EXPERIENCE
    Backend Developer
    Example Technologies
    2024 - Present
    Built REST APIs and maintained backend services.

    TECHNICAL SKILLS
    Languages: Python, JavaScript
    Backend: FastAPI, Django
    Databases: PostgreSQL, Redis
    Tools: Git, Docker

    EDUCATION
    BSc Computer Science
    """

    profile = CVProfileExtractor().extract(cv_text)

    assert profile["target_role"] == "PYTHON / BACKEND DEVELOPER"
    assert "Python" in profile["skills"]
    assert "FastAPI" in profile["skills"]
    assert "Django" in profile["skills"]
    assert "PostgreSQL" in profile["skills"]
    assert "Redis" in profile["skills"]
    assert "Git" in profile["skills"]
    assert "Docker" in profile["skills"]
    assert "Backend Developer" in profile["experience"]
