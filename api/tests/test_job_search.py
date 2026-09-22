"""Tests for generic job-search result filtering."""

from app.services.job_search import JobSearchService


def test_rejects_job_category_page():
    """Category pages should not be returned as individual jobs."""

    assert not JobSearchService._is_individual_job_result(
        "https://example.com/remote-customer-service-jobs/",
        "Remote Customer Service Jobs",
        "Browse remote customer service jobs and find new opportunities.",
    )


def test_rejects_job_search_page():
    """Search pages should not be returned as individual jobs."""

    assert not JobSearchService._is_individual_job_result(
        "https://example.com/jobs/search?query=customer+service",
        "Customer Service Jobs",
        "Search for jobs and view available positions.",
    )


def test_accepts_individual_customer_service_job():
    """A normal non-technical job posting should be accepted."""

    assert JobSearchService._is_individual_job_result(
        "https://example.com/jobs/customer-service-representative-123",
        "Customer Service Representative",
        (
            "We are hiring a Customer Service Representative. "
            "Responsibilities include supporting customers and resolving issues. "
            "Apply now."
        ),
    )


def test_accepts_individual_teacher_job():
    """A teaching job should be accepted without developer-specific logic."""

    assert JobSearchService._is_individual_job_result(
        "https://example.com/jobs/primary-school-teacher-123",
        "Primary School Teacher",
        (
            "We are hiring a Primary School Teacher. "
            "Requirements include classroom teaching experience. "
            "Apply now."
        ),
    )


def test_accepts_individual_healthcare_job():
    """A healthcare administration job should be accepted."""

    assert JobSearchService._is_individual_job_result(
        "https://example.com/jobs/healthcare-administrator-123",
        "Healthcare Administrator",
        (
            "This position is responsible for healthcare administration. "
            "Requirements include administrative experience. "
            "Apply now."
        ),
    )


def test_rejects_company_job_category_page():
    """Company career category pages should not be treated as individual jobs."""

    assert not JobSearchService._is_individual_job_result(
        "https://jobs.cvshealth.com/us/en/customer-care-jobs",
        "JOBS-Customer Care",
        "Explore customer care jobs and career opportunities.",
    )


def test_rejects_company_job_directory_page():
    """Company job directories should not be treated as individual jobs."""

    assert not JobSearchService._is_individual_job_result(
        "https://hiring.amazon.com/job-opportunities/customer-service-jobs",
        "Remote & In-Office Customer Service Jobs | Amazon",
        "Explore customer service jobs and available opportunities.",
    )


def test_rejects_company_careers_homepage():
    """A company careers homepage is not an individual job posting."""

    assert not JobSearchService._is_individual_job_result(
        "https://apply.workingsolutions.com/",
        "Working Solutions | Remote Customer Service Opportunities",
        "Explore remote customer service opportunities and apply today.",
    )


def test_rejects_remote_jobs_category_page():
    """Remote job category pages should not be treated as individual jobs."""

    assert not JobSearchService._is_individual_job_result(
        "https://nodesk.co/remote-jobs/customer-support/",
        "Remote Customer Support Jobs",
        "Browse remote customer support jobs and opportunities.",
    )


def test_rejects_company_customer_care_category():
    """Customer-care career categories should not be individual jobs."""

    assert not JobSearchService._is_individual_job_result(
        "https://careers.southwestair.com/us/en/customer-care/",
        "Customer Support and Services | Southwest",
        "Explore customer support and services career opportunities.",
    )


def test_rejects_company_experience_job_directory():
    """Company experience job directories should not be individual jobs."""

    assert not JobSearchService._is_individual_job_result(
        "https://careers.t-mobile.com/customer-experience-jobs",
        "Customer Experience Careers at T-Mobile",
        "Explore customer experience jobs and career opportunities.",
    )


def test_rejects_company_category_collection():
    """Company category collections should not be individual jobs."""

    assert not JobSearchService._is_individual_job_result(
        "https://careers.united.com/us/en/c/customer-solutions-jobs",
        "Customer Solutions jobs | Customer Solutions jobs at United Airlines",
        "Explore customer solutions jobs and career opportunities.",
    )

def test_rejects_remote_jobs_nested_category_page():
    assert not JobSearchService._is_individual_job_result(
        url="https://nodesk.co/remote-jobs/customer-support/",
        title="Remote Customer Support Jobs",
        snippet="Find remote customer support jobs.",
    )


def test_rejects_company_jobs_root_page():
    assert not JobSearchService._is_individual_job_result(
        url="https://careers.stryker.com/jobs",
        title="Jobs at Stryker | Stryker Careers",
        snippet="Explore open positions and careers at Stryker.",
    )


def test_rejects_company_customer_care_directory():
    assert not JobSearchService._is_individual_job_result(
        url="https://careers.southwestair.com/us/en/customer-care/",
        title="Customer Support and Services | Southwest",
        snippet="Explore customer care career opportunities.",
    )


def test_rejects_company_homepage():
    assert not JobSearchService._is_individual_job_result(
        url="https://join.liveops.com/",
        title="Liveops",
        snippet="Work from home customer service opportunities.",
    )

def test_rejects_remote_jobs_category_subdirectory():
    assert not JobSearchService._is_individual_job_result(
        url="https://nodesk.co/remote-jobs/customer-support/",
        title="Remote Customer Support Jobs",
        snippet="Find remote customer support jobs.",
    )


def test_rejects_customer_care_category_page():
    assert not JobSearchService._is_individual_job_result(
        url="https://careers.southwestair.com/us/en/customer-care/",
        title="Customer Support and Services | Southwest",
        snippet="Explore customer care career opportunities.",
    )


def test_rejects_homepage():
    assert not JobSearchService._is_individual_job_result(
        url="https://join.liveops.com/",
        title="Liveops",
        snippet="Work from home customer service opportunities.",
    )

def test_rejects_nodesk_remote_jobs_category_from_serper():
    assert not JobSearchService._is_individual_job_result(
        url="https://nodesk.co/remote-jobs/customer-support/",
        title="Remote Customer Support Jobs",
        snippet=(
            "Apply to all of the remote customer support jobs directly. "
            "No account required. Post a job."
        ),
    )

def test_rejects_customer_care_directory_path():
    assert not JobSearchService._is_individual_job_result(
        url="https://careers.southwestair.com/us/en/customer-care/",
        title="Customer Support and Services - Southwest Careers",
        snippet=(
            "Apply Now. Loyalty Assurance Representative. "
            "While working 100% remote, you'll assist Customers."
        ),
    )


def test_rejects_root_homepage_with_job_intent():
    assert not JobSearchService._is_individual_job_result(
        url="https://join.liveops.com/",
        title="Liveops Is Hiring | Join Liveops — Remote 1099 Jobs",
        snippet=(
            "Liveops is hiring. Join Liveops as a 1099 independent "
            "contractor for remote work from home jobs in customer service."
        ),
    )


def test_skips_job_page_when_page_extraction_fails(monkeypatch):
    """An inaccessible individual job page should not be returned."""

    service = JobSearchService()

    async def fail_extract(_url):
        raise RuntimeError("403 Forbidden")

    monkeypatch.setattr(service.extractor, "extract", fail_extract)

    result = {
        "link": "https://example.com/jobs/customer-service-agent",
        "title": "Customer Service Agent",
        "snippet": "We are hiring a Customer Service Agent. Apply now.",
    }

    import asyncio

    normalized = asyncio.run(
        service._normalize_result(
            result=result,
            location="Remote",
            employment_type=None,
        )
    )

    assert normalized is None
