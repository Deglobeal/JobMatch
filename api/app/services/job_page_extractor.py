"""Job-page extraction and normalization utilities."""

from dataclasses import dataclass
import json
import re

import httpx
from bs4 import BeautifulSoup


@dataclass
class ExtractedJob:
    """Normalized job information extracted from a job page."""
    title: str | None = None
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    description: str | None = None


class JobPageExtractor:
    """Extract and normalize structured job information."""

    # pylint: disable=too-few-public-methods

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/153.0.0.0 Safari/537.36"
            )
        }

    async def extract(self, url: str) -> ExtractedJob:
        """Fetch a job page and extract structured metadata."""

        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers=self.headers,
        ) as client:
            response = await client.get(url)

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        job_data = self._extract_job_posting_json_ld(soup)

        if job_data:
            return self._build_from_json_ld(job_data, soup)

        title = self._extract_job_title(soup)

        description = self._extract_meta(
            soup,
            [
                ("meta", {"property": "og:description"}),
                ("meta", {"name": "description"}),
            ],
        )

        description = self._clean_description(description)

        location = self._detect_remote(description)

        return ExtractedJob(
            title=title,
            location=location,
            description=description,
        )

    @staticmethod
    def _extract_job_posting_json_ld(
        soup: BeautifulSoup,
    ) -> dict | None:
        """Find JobPosting JSON-LD data on the page."""

        scripts = soup.find_all(
            "script",
            attrs={"type": "application/ld+json"},
        )

        for script in scripts:
            if not script.string:
                continue

            try:
                data = json.loads(script.string)
            except json.JSONDecodeError:
                continue

            candidates = data if isinstance(data, list) else [data]

            for item in candidates:
                if not isinstance(item, dict):
                    continue

                item_type = item.get("@type")

                if item_type == "JobPosting":
                    return item

                if (
                    isinstance(item_type, list)
                    and "JobPosting" in item_type
                ):
                    return item

        return None

    @staticmethod
    def _build_from_json_ld(
        data: dict,
        soup: BeautifulSoup,
    ) -> ExtractedJob:
        """Convert JobPosting JSON-LD into normalized data."""

        organization = data.get("hiringOrganization") or {}

        company = None

        if isinstance(organization, dict):
            company = organization.get("name")

        raw_description = data.get("description")

        description = JobPageExtractor._clean_description(
            raw_description
        )

        structured_location = JobPageExtractor._extract_location(
            data.get("jobLocation")
        )

        remote_location = JobPageExtractor._detect_remote(
            description
        )

        location = remote_location or structured_location

        employment_type = JobPageExtractor._normalize_employment_type(
            data.get("employmentType")
        )

        title = data.get("title")

        if not title:
            title = JobPageExtractor._extract_meta(
                soup,
                [
                    ("meta", {"property": "og:title"}),
                    ("meta", {"name": "twitter:title"}),
                ],
            )

        if not description:
            description = JobPageExtractor._clean_description(
                JobPageExtractor._extract_meta(
                    soup,
                    [
                        ("meta", {"property": "og:description"}),
                        ("meta", {"name": "description"}),
                    ],
                )
            )

        if not location:
            location = JobPageExtractor._detect_remote(
                description
            )

        return ExtractedJob(
            title=title,
            company=company,
            location=location,
            employment_type=employment_type,
            description=description,
        )

    @staticmethod
    def _extract_location(value) -> str | None:
        """Normalize a JobPosting jobLocation value."""

        if not value:
            return None

        locations = value if isinstance(value, list) else [value]

        location_values = []

        for location in locations:
            if not isinstance(location, dict):
                continue

            address = location.get("address")

            if isinstance(address, dict):
                parts = []

                for key in (
                    "streetAddress",
                    "addressLocality",
                    "addressRegion",
                    "addressCountry",
                ):
                    item = address.get(key)

                    if item:
                        parts.append(str(item))

                if parts:
                    location_values.append(", ".join(parts))

        if not location_values:
            return None

        return "; ".join(dict.fromkeys(location_values))

    @staticmethod
    def _normalize_employment_type(value) -> str | None:
        """Convert schema.org employment values into readable labels."""

        if not value:
            return None

        values = value if isinstance(value, list) else [value]

        labels = {
            "FULL_TIME": "Full-time",
            "PART_TIME": "Part-time",
            "CONTRACTOR": "Contract",
            "TEMPORARY": "Temporary",
            "INTERN": "Internship",
            "VOLUNTEER": "Volunteer",
            "PER_DIEM": "Per diem",
            "OTHER": "Other",
        }

        normalized = []

        for item in values:
            item = str(item).strip()

            if not item:
                continue

            normalized.append(
                labels.get(
                    item.upper(),
                    item.replace("_", " ").title(),
                )
            )

        if not normalized:
            return None

        return ", ".join(dict.fromkeys(normalized))

    @staticmethod
    def _detect_remote(description: str | None) -> str | None:
        """Detect remote work from the job description."""

        if not description:
            return None

        remote_patterns = [
            r"\b100%\s*remote\b",
            r"\bfully\s+remote\b",
            r"\bfully-remote\b",
            r"\bwork\s+from\s+home\b",
            r"\bremote\s+position\b",
            r"\bremote\s+role\b",
            r"\blocation\s*[:\-]\s*remote\b",
            r"\blocation\s*[:\-]\s*100%\s*remote\b",
            r"\blocation\s*[:\-]?\s*\*+\s*remote\b",
            r"\*+\s*location\s*[:\-]\s*remote\b",
        ]

        for pattern in remote_patterns:
            if re.search(
                pattern,
                description,
                flags=re.IGNORECASE,
            ):
                return "Remote"

        return None

    @staticmethod
    def _clean_description(
        description: str | None,
    ) -> str | None:
        """Remove HTML and normalize whitespace."""

        if not description:
            return None

        soup = BeautifulSoup(
            description,
            "html.parser",
        )

        text = soup.get_text(
            separator=" ",
            strip=True,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip() or None

    @staticmethod
    def _extract_job_title(
        soup: BeautifulSoup,
    ) -> str | None:
        """Extract a specific job title before falling back to metadata."""

        heading = soup.find("h1")

        if heading:
            title = heading.get_text(
                separator=" ",
                strip=True,
            )
            if title:
                return title

        return JobPageExtractor._extract_meta(
            soup,
            [
                ("meta", {"property": "og:title"}),
                ("meta", {"name": "twitter:title"}),
            ],
        )

    @staticmethod
    def _extract_meta(
        soup: BeautifulSoup,
        selectors: list[tuple[str, dict]],
    ) -> str | None:
        for tag_name, attributes in selectors:
            tag = soup.find(
                tag_name,
                attrs=attributes,
            )

            if tag and tag.get("content"):
                return tag["content"].strip()

        return None
