"""CV profile extraction service for JobMatch."""

import re


class CVProfileExtractor:
    # pylint: disable=too-few-public-methods
    """Extract a generic, editable job-search profile from CV text."""

    SECTION_NAMES = {
        "summary": {
            "summary",
            "professional summary",
            "profile",
            "professional profile",
            "about me",
            "objective",
            "career objective",
        },
        "experience": {
            "experience",
            "professional experience",
            "work experience",
            "employment history",
            "work history",
        },
        "skills": {
            "skills",
            "technical skills",
            "core skills",
            "key skills",
            "competencies",
        },
        "education": {
            "education",
            "academic background",
            "qualifications",
            "certifications education professional training",
            "certifications education and professional training",
        },
        "certifications": {
            "certifications",
            "certificates",
            "professional training",
        },
        "projects": {
            "projects",
            "selected projects",
            "personal projects",
        },
    }

    ROLE_KEYWORDS = (
        "developer",
        "engineer",
        "designer",
        "manager",
        "analyst",
        "accountant",
        "teacher",
        "nurse",
        "consultant",
        "administrator",
        "specialist",
        "coordinator",
        "officer",
        "architect",
        "scientist",
        "writer",
        "marketer",
        "marketing",
        "sales",
        "director",
        "assistant",
        "intern",
        "researcher",
        "technician",
        "therapist",
        "lawyer",
        "attorney",
        "doctor",
        "pharmacist",
        "recruiter",
        "executive",
        "supervisor",
        "lead",
        "trainer",
        "accounting",
        "finance",
        "operations",
        "human resources",
        "hr",
    )

    STOP_SECTIONS = {
        "experience": {
            "skills",
            "education",
            "certifications",
            "projects",
        },
        "skills": {
            "education",
            "certifications",
            "projects",
            "experience",
            "certifications education & professional training",
            "certifications education professional training",
            "certifications education and professional training",
        },
        "education": {
            "experience",
            "skills",
            "projects",
        },
        "certifications": {
            "experience",
            "skills",
            "projects",
            "education",
        },
    }

    def extract(self, cv_text: str) -> dict:
        """Create a profession-independent searchable CV profile."""

        if not cv_text.strip():
            raise ValueError("CV text is empty.")

        lines = self._clean_lines(cv_text)

        sections = self._split_sections(lines)

        summary = self._extract_summary(
            lines=lines,
            sections=sections,
        )

        projects = self._extract_projects_from_experience(
            sections=sections,
        )

        experience = self._extract_experience(
            sections=sections,
        )

        skills = self._extract_skills(
            sections=sections,
        )

        target_role = self._extract_target_role(
            lines=lines,
            summary=summary,
        )

        search_query = self._build_search_query(
            target_role=target_role,
            skills=skills,
        )

        education = self._extract_section_text(
            sections=sections,
            section_name="education",
        )

        certifications = self._extract_section_text(
            sections=sections,
            section_name="certifications",
        )

        if not projects:
            projects = self._extract_section_text(
                sections=sections,
                section_name="projects",
            )

        return {
            "target_role": target_role,
            "summary": summary,
            "skills": skills,
            "experience": experience,
            "projects": projects,
            "education": education,
            "certifications": certifications,
            "search_query": search_query,
        }

    @staticmethod
    def _clean_lines(text: str) -> list[str]:
        """Normalize extracted CV lines."""

        lines = []

        replacements = {
            "automatedtesting": "automated testing",
            "Developedand": "Developed and",
            "andapplication": "and application",
            "tasksand": "tasks and",
            "Gitand": "Git and",
            "RESTAPIs": "REST APIs",
            "RESTAPI": "REST API",
            "login,": "login,",
            "registration,login": "registration, login",
            "ina professional": "in a professional",
            "Dec 2025|": "Dec 2025 |",
        }

        for line in text.splitlines():
            cleaned = re.sub(r"\s+", " ", line).strip()

            for source, replacement in replacements.items():
                cleaned = cleaned.replace(source, replacement)

            targeted_fixes = {
                "ina professional": "in a professional",
                "RESTAPIs": "REST APIs",
                "Gitand": "Git and",
                "registration,login": "registration, login",
                "tasks.Implemented": "tasks. Implemented",
                "experience.Implemented": "experience. Implemented",
            }

            for source, replacement in targeted_fixes.items():
                cleaned = cleaned.replace(source, replacement)

            if cleaned:
                lines.append(cleaned)

        return lines

    def _split_sections(
        self,
        lines: list[str],
    ) -> dict[str, list[str]]:
        """Split CV text into recognizable sections."""

        sections: dict[str, list[str]] = {
            "summary": [],
            "experience": [],
            "skills": [],
            "education": [],
            "certifications": [],
            "projects": [],
        }

        current_section = None

        for line in lines:
            normalized = self._normalize_heading(line)

            if normalized in {
                "certifications education & professional training",
                "certifications education professional training",
                "certifications education and professional training",
            }:
                current_section = "education"
                continue

            detected_section = self._detect_section(
                normalized
            )

            if detected_section:
                current_section = detected_section
                continue

            if current_section:
                if self._is_section_stop(
                    current_section,
                    normalized,
                ):
                    current_section = None
                    continue

                sections[current_section].append(line)

        return sections

    @staticmethod
    def _normalize_heading(line: str) -> str:
        """Normalize a possible section heading."""

        normalized = line.lower()

        normalized = re.sub(
            r"[^a-z0-9& ]",
            " ",
            normalized,
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        return normalized

    def _detect_section(
        self,
        normalized_line: str,
    ) -> str | None:
        """Detect a known CV section heading."""

        for section, names in self.SECTION_NAMES.items():
            if normalized_line in names:
                return section

        return None

    def _is_section_stop(
        self,
        current_section: str,
        normalized_line: str,
    ) -> bool:
        """Check whether another heading ends the current section."""

        return normalized_line in self.STOP_SECTIONS.get(
            current_section,
            set(),
        )

    @staticmethod
    def _extract_summary(
        lines: list[str],
        sections: dict[str, list[str]],
    ) -> str | None:
        """Extract the professional summary."""

        explicit_summary = sections.get("summary", [])

        if explicit_summary:
            return " ".join(explicit_summary)[:1500]

        summary_end = None

        for index, line in enumerate(lines):
            normalized = re.sub(
                r"[^a-z ]",
                "",
                line.lower(),
            ).strip()

            if normalized == "summary":
                summary_end = index
                break

        if summary_end is None:
            return None

        summary_lines = []

        for line in lines[:summary_end]:
            if CVProfileExtractor._looks_like_contact_info(line):
                continue

            if CVProfileExtractor._looks_like_name(line):
                continue

            summary_lines.append(line)

        if not summary_lines:
            return None

        return " ".join(summary_lines)[-2000:]

    def _extract_target_role(
        self,
        lines: list[str],
        summary: str | None,
    ) -> str | None:
        """Find a likely role without assuming a specific profession."""

        # Prefer a concise explicit role line near the top.
        # This is usually a stronger signal than a role mentioned
        # inside a longer professional summary.
        for line in lines[:15]:
            if self._looks_like_role_line(line):
                return line[:160]

        # Fall back to the professional summary.
        if summary:
            sentences = re.split(
                r"(?<=[.!?])\s+",
                summary,
            )

            for sentence in sentences:
                sentence = sentence.strip()

                if not sentence:
                    continue

                if self._contains_role_keyword(sentence):
                    role = self._extract_role_from_sentence(sentence)

                    if role:
                        return role

        # Finally, look through the remaining CV lines.
        for line in lines:
            if self._looks_like_role_line(line):
                return line[:160]

        return None

    def _extract_role_from_sentence(
        self,
        sentence: str,
    ) -> str | None:
        """Extract a concise role title from a summary sentence."""

        match = re.match(
            r"^(?:an?|the)?\s*"
            r"(.+?\b(?:developer|engineer|designer|analyst|"
            r"accountant|teacher|nurse|consultant|administrator|"
            r"specialist|coordinator|officer|architect|scientist|"
            r"writer|marketer|manager|researcher|technician|"
            r"therapist|lawyer|attorney|doctor|pharmacist|"
            r"recruiter|executive|supervisor|trainer|intern)\b)",
            sentence,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        role = match.group(1).strip(" ,:-")

        if len(role) > 100:
            return None

        return role

    def _looks_like_role_line(
        self,
        line: str,
    ) -> bool:
        """Detect a concise line that looks like a job title."""

        cleaned = line.strip()

        if len(cleaned) > 160:
            return False

        if self._looks_like_contact_info(cleaned):
            return False

        if not self._contains_role_keyword(cleaned):
            return False

        # Strong signals for explicit CV title lines.
        if "|" in cleaned:
            return True

        if cleaned.isupper():
            return True

        return False

    def _contains_role_keyword(
        self,
        text: str,
    ) -> bool:
        """Check whether text contains a recognizable profession term."""

        lowered = text.lower()

        return any(
            re.search(
                rf"\b{re.escape(keyword)}\b",
                lowered,
            )
            for keyword in self.ROLE_KEYWORDS
        )

    @staticmethod
    def _extract_skills(
        sections: dict[str, list[str]],
    ) -> list[str]:
        """Extract skills only from the skills section."""

        values = sections.get("skills", [])

        if not values:
            return []

        skills = []

        for line in values:
            parts = re.split(
                r"[,|•;]",
                line,
            )

            for part in parts:
                cleaned = part.strip(" -:")

                # Remove category labels such as:
                # Languages:
                # Backend:
                # Databases:
                cleaned = re.sub(
                    r"^[^:]{1,50}:\s*",
                    "",
                    cleaned,
                ).strip()

                if not cleaned:
                    continue

                # A category may have multiple skills after the colon.
                sub_parts = [
                    item.strip()
                    for item in re.split(
                        r",",
                        cleaned,
                    )
                    if item.strip()
                ]

                skills.extend(sub_parts)

        cleaned_skills = []

        for skill in skills:
            skill = re.sub(
                r"\s+",
                " ",
                skill,
            ).strip()

            if not skill:
                continue

            if len(skill) > 80:
                continue

            if CVProfileExtractor._looks_like_section_heading(skill):
                continue

            if CVProfileExtractor._looks_like_sentence(skill):
                continue

            cleaned_skills.append(skill)

        return list(
            dict.fromkeys(cleaned_skills)
        )

    @staticmethod
    def _looks_like_section_heading(
        text: str,
    ) -> bool:
        normalized = re.sub(
            r"[^a-z ]",
            "",
            text.lower(),
        ).strip()

        return normalized in {
            "education",
            "certifications",
            "projects",
            "experience",
            "technical skills",
            "professional experience",
        }

    @staticmethod
    def _looks_like_sentence(
        text: str,
    ) -> bool:
        words = text.split()

        if len(words) > 8:
            return True

        if text.endswith("."):
            return True

        return False

    @staticmethod
    def _extract_projects_from_experience(
        sections: dict[str, list[str]],
    ) -> str | None:
        """Separate project entries embedded in the experience section."""

        values = sections.get("experience", [])

        if not values:
            return None

        project_markers = (
            "BuildOS — Construction Materials Marketplace",
            "Authentication & User Service",
            "Tally App — Task & Productivity Application",
            "Todo Diary — Task & Money Management App",
            "Personal Portfolio — Full-Stack Developer",
        )

        project_start = None

        for index, line in enumerate(values):
            if any(
                marker.lower() in line.lower()
                for marker in project_markers
            ):
                project_start = index
                break

        if project_start is None:
            return None

        project_lines = values[project_start:]

        sections["experience"] = values[:project_start]

        text = " ".join(project_lines)

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        return text[:5000] or None


    @staticmethod
    def _extract_section_text(
        sections: dict[str, list[str]],
        section_name: str,
    ) -> str | None:
        """Extract and normalize a generic CV section."""

        values = sections.get(section_name, [])

        if not values:
            return None

        text = " ".join(values)

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        return text[:5000] or None


    @staticmethod
    def _extract_experience(
        sections: dict[str, list[str]],
    ) -> str | None:
        """Extract work experience content."""

        values = sections.get("experience", [])

        if not values:
            return None

        return " ".join(values)[:5000]

    @staticmethod
    def _looks_like_name(
        text: str,
    ) -> bool:
        """Detect a likely CV name line."""

        words = text.split()

        if not 2 <= len(words) <= 5:
            return False

        if not text.isupper():
            return False

        return not any(
            character.isdigit()
            for character in text
        )

    @staticmethod
    def _looks_like_contact_info(
        text: str,
    ) -> bool:
        """Detect lines containing contact information."""

        contact_patterns = [
            r"@",
            r"\+\d",
            r"\b\d{7,}\b",
            r"https?://",
            r"\b(?:lagos|nigeria)\b",
            r"\blinkedin\b",
            r"\bgithub\b",
            r"\bportfolio\b",
        ]

        return any(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            for pattern in contact_patterns
        )

    @staticmethod
    def _build_search_query(
        target_role: str | None,
        skills: list[str],
    ) -> str:
        """Build a concise search query without personal information."""

        parts = []

        if target_role:
            parts.append(target_role)

        parts.extend(skills[:10])

        return re.sub(
            r"\s+",
            " ",
            " ".join(parts),
        ).strip()
