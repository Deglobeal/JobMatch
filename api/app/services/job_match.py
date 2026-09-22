"""Analyze how well a CV profile matches a job description."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class JobRequirement:
    """A requirement extracted from a job description."""

    text: str
    importance: str
    category: str


@dataclass
class JobMatchAnalysis:
    """Structured result of a CV-to-job comparison."""

    match_score: int
    matched_requirements: list[str]
    partial_matches: list[str]
    missing_requirements: list[str]
    requirement_details: list[dict]
    keywords: list[str]
    tailoring_suggestions: list[str]


class JobMatchService:
    """Compare a candidate profile with a job description."""

    STOP_WORDS = {
        "and",
        "the",
        "for",
        "with",
        "that",
        "this",
        "from",
        "your",
        "you",
        "our",
        "are",
        "will",
        "have",
        "has",
        "who",
        "what",
        "when",
        "where",
        "into",
        "their",
        "they",
        "them",
        "about",
        "using",
        "work",
        "working",
        "role",
        "team",
        "job",
        "years",
        "year",
        "experience",
        "required",
        "requirements",
        "preferred",
        "including",
        "such",
        "other",
        "more",
        "than",
        "also",
        "should",
        "must",
        "can",
        "able",
        "been",
        "being",
        "not",
        "all",
        "our",
        "its",
        "within",
        "across",
        "through",
        "well",
        "good",
        "strong",
        "looking",
    }

    GENERAL_REQUIREMENT_ALIASES = {
        "excel": "Excel",
        "quickbooks": "QuickBooks",
        "bookkeeping": "Bookkeeping",
        "financial reporting": "Financial Reporting",
        "customer service": "Customer Service",
        "communication": "Communication",
        "sales": "Sales",
        "negotiation": "Negotiation",
        "leadership": "Leadership",
        "project management": "Project Management",
        "organization": "Organization",
        "problem solving": "Problem Solving",
        "time management": "Time Management",
        "bachelor's degree": "Bachelor's Degree",
        "bachelor degree": "Bachelor's Degree",
        "master's degree": "Master's Degree",
        "master degree": "Master's Degree",
    }

    SKILL_ALIASES = {
        "rest api": "REST APIs",
        "rest apis": "REST APIs",
        "api": "REST APIs",
        "apis": "REST APIs",
        "fast api": "FastAPI",
        "fastapi": "FastAPI",
        "python": "Python",
        "django": "Django",
        "flask": "Flask",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "react": "React",
        "react native": "React Native",
        "node": "Node.js",
        "node.js": "Node.js",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "sqlite": "SQLite",
        "mongodb": "MongoDB",
        "sql": "SQL",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "Google Cloud",
        "google cloud": "Google Cloud",
        "git": "Git",
        "github": "GitHub",
        "gitlab": "GitLab",
        "ci/cd": "CI/CD",
        "cicd": "CI/CD",
        "pytest": "Pytest",
        "sqlalchemy": "SQLAlchemy",
        "jwt": "JWT",
        "authentication": "Authentication",
        "authorization": "Authorization",
        "tailwind": "Tailwind CSS",
        "html": "HTML",
        "html5": "HTML5",
        "css": "CSS",
        "css3": "CSS3",
    }

    def analyze(
        self,
        cv_profile: dict,
        job_description: str,
        job_title: str | None = None,
    ) -> JobMatchAnalysis:
        """Analyze a CV profile against a job description."""

        cv_text = self._profile_to_text(cv_profile)
        job_text = " ".join(
            item
            for item in [job_title or "", job_description]
            if item
        )

        job_lower = job_text.lower()
        cv_lower = cv_text.lower()

        requirements = self._extract_requirements(job_lower)
        keywords = self._extract_keywords(job_lower)

        matched = []
        partial = []
        missing = []
        requirement_details = []

        for requirement in requirements:
            requirement_text = requirement.text
            requirement_lower = requirement_text.lower()

            if self._contains_term(cv_lower, requirement_lower):
                status = "matched"
                matched.append(requirement_text)
            elif self._has_partial_match(cv_lower, requirement_lower):
                status = "partial"
                partial.append(requirement_text)
            else:
                status = "missing"
                missing.append(requirement_text)

            requirement_details.append(
                {
                    "text": requirement_text,
                    "importance": requirement.importance,
                    "status": status,
                    "category": requirement.category,
                }
            )

        total_weight = sum(
            1.0 if item.importance == "required" else 0.5
            for item in requirements
        )

        if total_weight == 0:
            score = 0
        else:
            earned_weight = 0.0

            for item in requirements:
                if item.text in matched:
                    earned_weight += (
                        1.0
                        if item.importance == "required"
                        else 0.5
                    )
                elif item.text in partial:
                    earned_weight += (
                        0.5
                        if item.importance == "required"
                        else 0.25
                    )

            score = round(
                earned_weight / total_weight * 100
            )

        suggestions = [
            (
                f"Add truthful evidence of {item} "
                "if you have this experience."
            )
            for item in missing
        ]

        suggestions.extend(
            (
                f"Strengthen the CV evidence for {item} "
                "using a concrete project, responsibility, "
                "or measurable result."
            )
            for item in partial
        )

        return JobMatchAnalysis(
            match_score=max(0, min(score, 100)),
            matched_requirements=matched,
            partial_matches=partial,
            missing_requirements=missing,
            requirement_details=requirement_details,
            keywords=keywords,
            tailoring_suggestions=suggestions,
        )

    @classmethod
    def _requirement_category(cls, requirement: str) -> str:
        """Classify a recognized requirement into a general job category."""

        requirement_lower = requirement.lower()

        if requirement_lower in {
            "bachelor's degree",
            "bachelor degree",
            "master's degree",
            "master degree",
        }:
            return "education"

        if requirement_lower in {
            "authentication",
            "authorization",
            "communication",
            "leadership",
            "negotiation",
            "organization",
            "problem solving",
            "time management",
            "customer service",
        }:
            return "skill"

        if requirement_lower in {
            "bookkeeping",
            "financial reporting",
            "project management",
            "sales",
        }:
            return "skill"

        if requirement in cls.SKILL_ALIASES.values():
            return "skill"

        if requirement in cls.GENERAL_REQUIREMENT_ALIASES.values():
            return "skill"

        return "other"

    def _profile_to_text(self, profile: dict) -> str:
        """Flatten a CV profile into searchable text."""

        values = []

        for key in (
            "target_role",
            "summary",
            "skills",
            "experience",
            "projects",
            "education",
            "certifications",
        ):
            value = profile.get(key)

            if value is None:
                continue

            if isinstance(value, list):
                values.extend(str(item) for item in value)
            elif isinstance(value, dict):
                values.extend(str(item) for item in value.values())
            else:
                values.append(str(value))

        return " ".join(values)

    def _extract_requirements(
        self,
        job_text: str,
    ) -> list[JobRequirement]:
        """Extract recognizable requirements with importance and category."""

        found = []

        vocabularies = (
            self.GENERAL_REQUIREMENT_ALIASES,
            self.SKILL_ALIASES,
        )

        required_context = re.compile(
            r"\b(required|required qualifications|must have|must|required skills)\b",
            flags=re.IGNORECASE,
        )
        preferred_context = re.compile(
            r"\b(preferred|preferred qualifications|nice to have|bonus|desired)\b",
            flags=re.IGNORECASE,
        )

        for vocabulary in vocabularies:
            for phrase, label in vocabulary.items():
                pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
                match = re.search(pattern, job_text, flags=re.IGNORECASE)

                if not match or any(item.text == label for item in found):
                    continue

                preceding_text = job_text[:match.start()]
                last_required = list(required_context.finditer(preceding_text))
                last_preferred = list(preferred_context.finditer(preceding_text))

                required_position = (
                    last_required[-1].start()
                    if last_required
                    else -1
                )
                preferred_position = (
                    last_preferred[-1].start()
                    if last_preferred
                    else -1
                )

                importance = (
                    "preferred"
                    if preferred_position > required_position
                    else "required"
                )

                found.append(
                    JobRequirement(
                        text=label,
                        importance=importance,
                        category=self._requirement_category(label),
                    )
                )

        return found

    def _extract_keywords(
        self,
        job_text: str,
    ) -> list[str]:
        """Extract useful recurring job-description keywords."""

        words = re.findall(
            r"\b[a-zA-Z][a-zA-Z0-9+#./-]{2,}\b",
            job_text,
        )

        keywords = []

        for word in words:
            normalized = word.lower().strip(".,;:()[]{}")

            if normalized in self.STOP_WORDS:
                continue

            if normalized not in {
                item.lower() for item in keywords
            }:
                keywords.append(word)

        return keywords[:40]

    @staticmethod
    def _contains_term(
        text: str,
        term: str,
    ) -> bool:
        """Return whether a normalized term exists in text."""

        if term in text:
            return True

        singular = term.rstrip("s")

        return singular != term and singular in text

    @staticmethod
    def _has_partial_match(
        text: str,
        requirement: str,
    ) -> bool:
        """Detect related evidence without claiming an exact match."""

        related_terms = {
            "rest apis": ["api", "http"],
            "fastapi": ["python", "api"],
            "postgresql": ["sql", "database"],
            "docker": [
                "container",
                "containerized",
                "docker compose",
                "dockerfile",
            ],
            "aws": [
                "amazon web services",
                "aws sdk",
                "aws console",
                "aws ec2",
                "aws s3",
                "aws lambda",
                "aws ecs",
                "aws eks",
                "aws elastic beanstalk",
                "aws cloudformation",
            ],
            "ci/cd": ["deployment", "deployed", "deploy", "github", "gitlab"],
            "react": ["javascript", "frontend"],
            "react native": ["react", "javascript"],
            "authentication": ["jwt", "authorization"],
            "authorization": ["authentication", "rbac"],
        }

        terms = related_terms.get(requirement.lower(), [])

        return any(
            term in text
            for term in terms
        )

    @staticmethod
    def _keyword_score(
        keywords: list[str],
        cv_text: str,
    ) -> int:
        """Calculate a fallback keyword-overlap score."""

        if not keywords:
            return 0

        matched = sum(
            1
            for keyword in keywords
            if keyword.lower() in cv_text
        )

        return round(
            matched / len(keywords) * 100
        )
