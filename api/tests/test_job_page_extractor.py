"""Tests for job-page extraction."""

from bs4 import BeautifulSoup

from app.services.job_page_extractor import JobPageExtractor


def test_extracts_job_posting_from_json_ld():
    """A JobPosting JSON-LD block should produce normalized job data."""

    html = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "JobPosting",
                "title": "Customer Service Representative",
                "description": "We are hiring a customer service representative.",
                "hiringOrganization": {
                    "@type": "Organization",
                    "name": "Example Company"
                },
                "jobLocation": {
                    "@type": "Place",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "Lagos",
                        "addressCountry": "NG"
                    }
                },
                "employmentType": "FULL_TIME"
            }
            </script>
        </head>
    </html>
    """

    soup = BeautifulSoup(html, "html.parser")
    data = JobPageExtractor._extract_job_posting_json_ld(soup)

    result = JobPageExtractor._build_from_json_ld(data, soup)

    assert result.title == "Customer Service Representative"
    assert result.company == "Example Company"
    assert result.location == "Lagos, NG"
    assert result.employment_type == "Full-time"
    assert "customer service representative" in result.description


def test_extracts_specific_job_title_from_mci_style_metadata():
    """A job-specific page should not use a generic careers title."""

    html = """
    <html>
        <head>
            <title>Careers | MCI | A Culture of Excellence | Join Our Team</title>
            <meta
                property="og:title"
                content="Careers | MCI | A Culture of Excellence | Join Our Team"
            >
            <meta
                name="description"
                content="MCI is a world leader in advanced, tech-enabled BPO."
            >
        </head>
        <body>
            <h1>Technical Customer Care Representative I (Entry Level)</h1>
        </body>
    </html>
    """

    soup = BeautifulSoup(html, "html.parser")

    title = JobPageExtractor._extract_job_title(soup)

    assert title == "Technical Customer Care Representative I (Entry Level)"
