"""Job search service for discovering and normalizing real job postings."""

# pylint: disable=too-few-public-methods

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.providers.serper import SerperSearchProvider
from app.services.job_page_extractor import JobPageExtractor


@dataclass
class JobSearchResult:
    """Normalized job search result."""

    title: str
    company: str | None
    location: str | None
    employment_type: str | None
    description: str | None
    source: str
    url: str


class JobSearchService:
    """Search for real individual job postings through Google/Serper."""

    def __init__(self):
        self.provider = SerperSearchProvider()
        self.extractor = JobPageExtractor()

    @staticmethod
    def _build_base_query(
        query: str,
        location: str | None = None,
        employment_type: str | None = None,
        experience_level: str | None = None,
    ) -> str:
        """Build the common search terms used by targeted queries."""

        parts = [query]

        if location:
            parts.append(location)

        if employment_type:
            parts.append(employment_type)

        if experience_level:
            parts.append(experience_level)

        return " ".join(parts)

    @staticmethod
    def _build_search_queries(
        query: str,
        location: str | None = None,
        employment_type: str | None = None,
        experience_level: str | None = None,
    ) -> list[str]:
        """Build multiple targeted search queries for individual job postings."""

        parts = [query]

        if location:
            parts.append(location)

        if employment_type:
            parts.append(employment_type)

        if experience_level:
            parts.append(experience_level)

        base_query = " ".join(parts)

        return [
            f'{base_query} "Apply"',
            f'{base_query} "Apply now"',
            f'{query} {location or ""} "Apply"',
            f'{query} {location or ""} "Apply now"',
        ]

    @staticmethod
    def _is_relevant_job(
        query: str,
        title: str,
        description: str | None,
    ) -> bool:
        """Check whether a result has meaningful overlap with the search query."""

        query_terms = {
            term.lower()
            for term in query.split()
            if len(term) >= 3
        }

        if not query_terms:
            return False

        searchable_text = " ".join(
            [
                title,
                description or "",
            ]
        ).lower()

        matched_terms = [
            term
            for term in query_terms
            if term in searchable_text
        ]

        return bool(matched_terms)

    @staticmethod
    # pylint: disable=too-many-return-statements
    def _is_likely_job_page(url: str, title: str) -> bool:
        """Reject obvious search, category, social, and job-index pages."""

        parsed = urlparse(url)

        hostname = (
            parsed.hostname or ""
        ).lower().removeprefix("www.")

        path = parsed.path.lower()
        query_string = parsed.query.lower()
        title_lower = title.lower()

        blocked_domains = {
            "reddit.com",
            "facebook.com",
            "x.com",
            "twitter.com",
            "youtube.com",
            "tiktok.com",
            "instagram.com",
            "dev.to",
            "medium.com",
        }

        blocked_domains_with_job_indexes = {
            "indeed.com",
            "ziprecruiter.com",
            "jobstreet.com",
            "jobsdb.com",
        }

        blocked_path_patterns = [
            "/search",
            "/job-search",
            "/jobs/search",
            "/jobs/category",
            "/jobs/q-",
            "/job-category",
            "/job-categories",
            "/job-offers/all",
            "/community/jobs",
            "/q-remote-",
            "/role/",
        ]

        blocked_query_patterns = [
            "q=",
            "query=",
            "search=",
            "keyword=",
        ]

        blocked_title_patterns = [
            "jobs in",
            "jobs -",
            "job search",
            "job openings",
            "jobs (",
            "jobs |",
            "job offers",
            "find jobs",
            "search jobs",
            "job listings",
            "jobs found",
            "jobs, hiring",
        ]

        if hostname in blocked_domains:
            return False

        if any(
            hostname.endswith(f".{domain}")
            for domain in blocked_domains
        ):
            return False

        if hostname in blocked_domains_with_job_indexes:
            return False

        if any(
            pattern in path
            for pattern in blocked_path_patterns
        ):
            return False

        if any(
            pattern in query_string
            for pattern in blocked_query_patterns
        ):
            return False

        if any(
            pattern in title_lower
            for pattern in blocked_title_patterns
        ):
            return False

        return True

    @staticmethod
    # pylint: disable=too-many-return-statements
    def _is_individual_job_result(
        url: str,
        title: str,
        snippet: str | None,
    ) -> bool:
        """Check whether a search result appears to be an individual job."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        text = " ".join([title, snippet or ""]).lower()

        if JobSearchService._has_index_path(path):
            return False

        if JobSearchService._is_root_path(path):
            return False

        if JobSearchService._has_category_path(path):
            return False

        if JobSearchService._has_index_title(title):
            return False

        if JobSearchService._has_index_snippet(text):
            return False

        if JobSearchService._has_directory_path_without_job(path):
            return False

        return JobSearchService._has_job_intent(text)

    @staticmethod
    def _has_index_path(path: str) -> bool:
        """Return whether a path clearly represents a job index."""
        patterns = [
            "/search",
            "/job-search",
            "/jobs/search",
            "/jobs/category",
            "/job-category",
            "/job-categories",
            "/job-offers/all",
            "/community/jobs",
            "/q-remote-",
            "/role/",
            "/remote-jobs/",
        ]
        return any(pattern in path for pattern in patterns)

    @staticmethod
    def _is_root_path(path: str) -> bool:
        """Return whether the URL points to a site homepage."""
        return path.rstrip("/") == ""

    @staticmethod
    def _has_category_path(path: str) -> bool:
        """Return whether a path appears to be a job category."""
        patterns = [
            "-jobs",
            "-job",
            "-careers",
            "-career",
            "-opportunities",
            "-opportunity",
            "/customer-care/",
            "/customer-service/",
            "/customer-support/",
        ]
        normalized_path = path.rstrip("/")
        normalized_patterns = [
            pattern.rstrip("/")
            for pattern in patterns
        ]
        return any(
            normalized_path.endswith(pattern)
            for pattern in normalized_patterns
        )

    @staticmethod
    def _has_index_title(title: str) -> bool:
        """Return whether a title clearly represents a job index or article."""
        patterns = [
            "how to",
            "how do you",
            "how do i",
            "guide to",
            "guide:",
            "tips for",
            "tips to",
            "ways to",
            "things to know",
            "what you need to know",
            "everything you need to know",
            "needs to know",
            "best practices",
            "career advice",
            "job boards",
            "job search tips",
            "job hunting tips",
            "resume tips",
            "interview tips",
            "remote python jobs",
            "remote django jobs",
            "remote fastapi developer jobs",
            "python developer jobs",
            "junior django jobs",
            "junior python jobs",
            "jobs in ",
            "jobs found",
            "find jobs",
            "search jobs",
            "job listings",
            "job openings",
            "top ",
            "customer service jobs",
            "customer care jobs",
            "career opportunities",
            "remote customer service opportunities",
        ]
        title_lower = title.lower()
        return any(pattern in title_lower for pattern in patterns)

    @staticmethod
    def _has_index_snippet(text: str) -> bool:
        """Return whether a snippet clearly represents a job index."""
        patterns = [
            "search the best",
            "find remote",
            "see salaries, compare",
            "new jobs added daily",
            "jobs available",
            "find the best remote",
            "compare salary",
            "search for jobs",
            "view all our",
            "explore job opportunities",
            "explore customer service jobs",
            "explore customer care jobs",
        ]
        return any(pattern in text for pattern in patterns)

    @staticmethod
    def _has_directory_path_without_job(path: str) -> bool:
        """Return whether a directory path lacks individual-job evidence."""
        directory_patterns = [
            "/careers/",
            "/career/",
            "/jobs/",
            "/job/",
            "/opportunities/",
        ]
        individual_patterns = [
            "/apply/",
            "/job/",
            "/jobs/",
            "/position/",
            "/positions/",
            "/posting/",
            "/postings/",
            "/vacancy/",
            "/vacancies/",
        ]

        has_directory = (
            any(pattern in path for pattern in directory_patterns)
            or path.rstrip("/") in {
                "/jobs",
                "/job",
                "/careers",
                "/career",
                "/opportunities",
            }
        )
        has_individual = any(
            pattern in path
            for pattern in individual_patterns
        )

        return has_directory and not has_individual

    @staticmethod
    def _has_job_intent(text: str) -> bool:
        """Return whether text contains evidence of an individual job."""
        terms = [
            "apply",
            "responsibilities",
            "requirements",
            "qualifications",
            "job description",
            "experience",
            "we are hiring",
            "hiring",
            "position",
            "role",
        ]
        return any(term in text for term in terms)

    @staticmethod
    def _matches_experience_level(
        experience_level: str | None,
        title: str,
        snippet: str | None,
    ) -> bool:
        """Check whether a result matches the requested experience level."""

        if not experience_level:
            return True

        if experience_level.lower() != "junior":
            return True

        text = " ".join(
            [
                title,
                snippet or "",
            ]
        ).lower()

        excluded_terms = [
            "senior",
            "sr.",
            "sr ",
            "lead developer",
            "lead engineer",
            "principal",
            "staff engineer",
            "engineering manager",
            "director of",
            "head of",
            "5+ years",
            "6+ years",
            "7+ years",
            "8+ years",
            "10+ years",
        ]

        return not any(
            term in text
            for term in excluded_terms
        )

    async def _normalize_result(
        self,
        result: dict,
        location: str | None,
        employment_type: str | None,
    ) -> JobSearchResult:
        """Extract and normalize one job search result."""

        url = result["link"]
        title = result["title"]
        snippet = result.get("snippet")

        hostname = (
            urlparse(url).hostname or ""
        ).lower().removeprefix("www.")

        try:
            extracted = await self.extractor.extract(url)
        except (httpx.HTTPError, ValueError, RuntimeError) as error:
            print(
                f"Skipping job page {url}: "
                f"{type(error).__name__}: {error}"
            )
            return None

        if not extracted:
            return None

        return JobSearchResult(
            title=extracted.title or title,
            company=extracted.company,
            location=extracted.location or location,
            employment_type=(
                extracted.employment_type
                or employment_type
            ),
            description=(
                extracted.description
                or snippet
            ),
            source=hostname,
            url=url,
        )

    async def search(
        self,
        query: str,
        location: str | None = None,
        employment_type: str | None = None,
        experience_level: str | None = None,
    ) -> list[JobSearchResult]:
        """Search multiple targeted queries and normalize real job results."""

        search_queries = self._build_search_queries(
            query=query,
            location=location,
            employment_type=employment_type,
            experience_level=experience_level,
        )

        jobs: list[JobSearchResult] = []
        seen_urls: set[str] = set()

        for search_query in search_queries:
            try:
                results = await self.provider.search(
                    search_query,
                    num=10,
                )
            except (httpx.HTTPError, RuntimeError) as error:
                print(
                    f"Search failed for query '{search_query}': "
                    f"{type(error).__name__}: {error}"
                )
                continue

            for result in results:
                url = result.get("link")
                title = result.get("title", "").strip()
                snippet = result.get("snippet")

                if not url or not title:
                    continue

                if url in seen_urls:
                    continue

                if not self._is_likely_job_page(
                    url=url,
                    title=title,
                ):
                    continue

                if not self._is_individual_job_result(
                    url=url,
                    title=title,
                    snippet=snippet,
                ):
                    continue

                if not self._is_relevant_job(
                    query=query,
                    title=title,
                    description=snippet,
                ):
                    continue

                if not self._matches_experience_level(
                    experience_level=experience_level,
                    title=title,
                    snippet=snippet,
                ):
                    continue

                normalized_job = await self._normalize_result(
                    result=result,
                    location=location,
                    employment_type=employment_type,
                )

                if normalized_job is None:
                    continue

                seen_urls.add(url)
                jobs.append(normalized_job)

                if len(jobs) >= 10:
                    return jobs

        return jobs
