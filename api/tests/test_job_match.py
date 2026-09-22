"""Tests for the general-purpose JobMatch analysis service."""

from app.services.job_match import JobMatchService


def test_job_match_supports_non_technical_roles():
    service = JobMatchService()

    cv_profile = {
        "target_role": "Accountant",
        "summary": (
            "Accountant with experience preparing financial reports "
            "and maintaining accurate records."
        ),
        "skills": [
            "Excel",
            "Bookkeeping",
            "Financial Reporting",
        ],
        "experience": [
            "Prepared monthly financial reports.",
            "Maintained accounting records.",
        ],
        "education": [
            "Bachelor's degree in Accounting",
        ],
    }

    job_description = """
    We are looking for an Accountant with experience in bookkeeping,
    financial reporting, Excel, and maintaining accurate accounting records.
    A bachelor's degree in Accounting is required.
    """

    result = service.analyze(
        cv_profile=cv_profile,
        job_description=job_description,
        job_title="Accountant",
    )

    assert 0 <= result.match_score <= 100
    assert result.matched_requirements
    assert isinstance(result.partial_matches, list)
    assert isinstance(result.missing_requirements, list)
    assert isinstance(result.tailoring_suggestions, list)


def test_job_match_does_not_claim_100_percent_when_requirements_are_unknown():
    service = JobMatchService()

    cv_profile = {
        "target_role": "Professional",
        "summary": "Customer-focused professional.",
        "skills": ["Communication"],
    }

    result = service.analyze(
        cv_profile=cv_profile,
        job_description=(
            "Join our growing organization and contribute "
            "to our long-term goals."
        ),
        job_title="Professional",
    )

    assert 0 <= result.match_score < 100


def test_job_match_distinguishes_required_and_preferred_requirements():
    service = JobMatchService()

    cv_profile = {
        "target_role": "Accountant",
        "summary": "Accountant experienced in financial reporting.",
        "skills": [
            "Excel",
            "Financial Reporting",
        ],
        "experience": [
            "Prepared monthly financial reports.",
        ],
    }

    job_description = """
    Required:
    Excel and financial reporting.

    Preferred:
    Bookkeeping and QuickBooks.
    """

    result = service.analyze(
        cv_profile=cv_profile,
        job_description=job_description,
        job_title="Accountant",
    )

    assert "Excel" in result.matched_requirements
    assert "Financial Reporting" in result.matched_requirements
    assert "Bookkeeping" in result.missing_requirements
    assert "QuickBooks" in result.missing_requirements

    details = {
        item["text"]: item
        for item in result.requirement_details
    }

    assert details["Excel"]["importance"] == "required"
    assert details["Excel"]["status"] == "matched"
    assert details["Excel"]["category"] == "skill"

    assert details["Financial Reporting"]["importance"] == "required"
    assert details["Financial Reporting"]["status"] == "matched"

    assert details["Bookkeeping"]["importance"] == "preferred"
    assert details["Bookkeeping"]["status"] == "missing"
    assert details["Bookkeeping"]["category"] == "skill"

    assert details["QuickBooks"]["importance"] == "preferred"
    assert details["QuickBooks"]["status"] == "missing"

    assert result.match_score == 67
