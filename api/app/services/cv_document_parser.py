"""Deterministic parsing helpers for structured CV documents."""

import re

from app.services.cv_document import CVDocument, CVLink, CVPersonalDetails


URL_PATTERN = re.compile(
    r"https?://(?:www\.)?[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
    r"(?:/[^\s|]*)?"
    r"|(?:(?<=---)|(?<![A-Za-z0-9@._-]))"
    r"(?:www\.)?[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
    r"(?:/[^\s|]*)?",
    re.IGNORECASE,
)

EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"
)

LINKEDIN_PATTERN = re.compile(
    r"https?://(?:www\.)?linkedin\.com/[^\s|]+",
    re.IGNORECASE,
)

GITHUB_PATTERN = re.compile(
    r"https?://(?:www\.)?github\.com/[^\s|]+",
    re.IGNORECASE,
)


class CVDocumentParser:
    """Build deterministic CV document metadata from extracted text."""

    def parse(self, cv_text: str) -> CVDocument:
        """Parse deterministic professional details from CV text."""

        cleaned_text = cv_text.strip()

        if not cleaned_text:
            raise ValueError("CV content is required.")

        header = self._extract_header(cleaned_text)

        personal = CVPersonalDetails(
            name=header["name"],
            headline=header["headline"],
            location=header["location"],
            email=self._extract_first(EMAIL_PATTERN, cleaned_text),
            phone=self._extract_phone(cleaned_text),
            links=self._extract_links(self._extract_header_text(cleaned_text)),
        )

        return CVDocument(
            personal=personal,
            source_text=cleaned_text,
        )

    @staticmethod
    def _extract_header_text(text: str) -> str:
        """Return the personal header section before summary/body content."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ""

        header_lines = []

        for line in lines:
            if line.upper() in {
                "SUMMARY",
                "PROFESSIONAL SUMMARY",
                "PROFESSIONAL EXPERIENCE",
                "EXPERIENCE",
                "WORK EXPERIENCE",
                "EDUCATION",
                "PROJECTS",
                "SKILLS",
            }:
                break

            if (
                "@" in line
                or "linkedin.com" in line.lower()
                or "github.com" in line.lower()
                or "portfolio" in line.lower()
                or re.search(r"https?://|www\.", line, re.IGNORECASE)
            ):
                header_lines.append(line)
                continue

            if len(header_lines) < 3:
                header_lines.append(line)
            else:
                break

        return "\n".join(header_lines)

    @staticmethod
    def _extract_header(text: str) -> dict[str, str | None]:
        """Extract likely name, headline, and location from the CV header."""

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        if not lines:
            return {
                "name": None,
                "headline": None,
                "location": None,
            }

        header_lines = lines[:6]

        name = header_lines[0] if header_lines else None

        headline = None
        if len(header_lines) > 1:
            candidate = header_lines[1]

            if (
                "@" not in candidate
                and "http://" not in candidate.lower()
                and "https://" not in candidate.lower()
            ):
                headline = candidate

        location = None

        for line in header_lines[:4]:
            location_match = re.search(
                r"(^|\|)\s*([^|]+?)\s*,\s*"
                r"(Nigeria|Ghana|Kenya|United Kingdom|United States|"
                r"Canada|Australia)\s*(\||$)",
                line,
                re.IGNORECASE,
            )

            if location_match:
                location = (
                    f"{location_match.group(2).strip()}, "
                    f"{location_match.group(3).strip()}"
                )
                break

        return {
            "name": name,
            "headline": headline,
            "location": location,
        }

    @staticmethod
    def _extract_first(
        pattern: re.Pattern[str],
        text: str,
    ) -> str | None:
        match = pattern.search(text)

        if not match:
            return None

        return match.group(0).rstrip(".,);]")

    @staticmethod
    def _extract_phone(text: str) -> str | None:
        for match in PHONE_PATTERN.finditer(text):
            value = match.group(0).strip()
            digits = re.sub(r"\D", "", value)

            if 8 <= len(digits) <= 15:
                return value

        return None

    @staticmethod
    @staticmethod
    def _extract_links(text: str) -> list[CVLink]:
        links: list[CVLink] = []
        seen_urls: set[str] = set()

        for match in URL_PATTERN.finditer(text):
            raw_url = match.group(0).rstrip(".,);]")

            # PDF extraction can attach visible link labels or delimiter
            # artifacts directly to the URL, for example:
            # "Remote Demo ----buildoshub.vercel.app"
            # "Demo---drive.google.com/..."
            normalized = re.sub(
                r"^(?:[A-Za-z][A-Za-z ]{1,40}---|---+)",
                "",
                raw_url,
            ).strip()

            if not normalized:
                continue

            # Find the actual URL position inside the original match so
            # label inference sees the text immediately before the URL.
            url_offset = raw_url.find(normalized)

            if url_offset < 0:
                continue

            url = normalized
            url_start = match.start() + url_offset

            if url in seen_urls:
                continue

            seen_urls.add(url)

            label = CVDocumentParser._infer_link_label(
                url=url,
                text=text,
                start=url_start,
            )

            links.append(
                CVLink(
                    label=label,
                    url=url,
                )
            )

        return links

    def extract_link_contexts(self, text: str) -> list[dict[str, str]]:
        """Return explicit URL, label, and source-line context."""

        return self._extract_link_contexts(text)

    @staticmethod
    def _extract_link_contexts(text: str) -> list[dict[str, str]]:
        """Extract explicit links together with their source line context."""

        contexts: list[dict[str, str]] = []

        for match in URL_PATTERN.finditer(text):
            raw_url = match.group(0).rstrip(".,);]")

            url = re.sub(
                r"^(?:-{3,}|[A-Za-z][A-Za-z ]*-{3,})",
                "",
                raw_url,
            )

            if not url:
                continue

            url_offset = raw_url.find(url)
            url_start = match.start() + (
                url_offset if url_offset >= 0 else 0
            )

            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.start())

            if line_end == -1:
                line_end = len(text)

            line = text[line_start:line_end].strip()

            contexts.append(
                {
                    "url": url,
                    "line": line,
                    "label": CVDocumentParser._infer_link_label(
                        url=url,
                        text=text,
                        start=url_start,
                    ),
                }
            )

        return contexts

    @staticmethod
    def _infer_link_label(
        *,
        url: str,
        text: str,
        start: int,
    ) -> str:
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", start)

        if line_end == -1:
            line_end = len(text)

        line = text[line_start:line_end]
        prefix = line[: start - line_start].strip()

        # PDF extraction may attach the URL directly to a visible
        # link label, for example "Remote Demo ----URL" or
        # "Demo---URL". Prefer a recognizable link-label phrase
        # from the end of the prefix so project titles are not
        # incorrectly returned as labels.
        link_label_pattern = re.compile(
            r"(?P<label>"
            r"(?:remote\s+demo|live\s+demo|demo(?:\s+link)?|"
            r"api\s+docs?|documentation|docs?|portfolio|"
            r"github|linkedin|website|repository|source\s+code)"
            r")\s*[-:|]+\s*$",
            re.IGNORECASE,
        )

        label_match = link_label_pattern.search(prefix)

        if label_match:
            return label_match.group("label").strip()

        # Handle ordinary explicit labels such as "API Docs: URL".
        label_match = re.search(
            r"([A-Za-z][A-Za-z ]{1,40})\s*:\s*$",
            prefix,
        )

        if label_match:
            return label_match.group(1).strip()

        if LINKEDIN_PATTERN.fullmatch(url):
            return "LinkedIn"

        if GITHUB_PATTERN.fullmatch(url):
            return "GitHub"

        if "portfolio" in prefix.lower():
            return "Portfolio"

        return "Link"
