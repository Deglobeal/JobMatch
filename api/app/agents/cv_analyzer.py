"""JobMatch Agent 2: CV Analyst."""

from typing import cast

from app.ai.gemini_provider import GeminiProvider
from app.agents.cv_agent import CVAnalysis


class CVAnalyzer:
    """Analyze CV content using the configured AI provider."""

    SYSTEM_PROMPT = """
You are JobMatch Agent 2, a CV Analyst.

Your task is to analyze only the supplied CV content and extract
structured candidate information.

Rules:
1. Analyze only the supplied CV.
2. Do not infer qualifications, experience, skills, or achievements
   that are not supported by the CV.
3. Preserve factual meaning from the CV.
4. Identify the candidate's likely roles and seniority only when
   supported by the CV.
5. Separate responsibilities from achievements where possible.
6. Extract the location for each experience entry when explicitly stated.
7. Extract the start date for each experience entry when explicitly stated.
8. Extract the end date for each experience entry when explicitly stated.
9. If an experience date is marked as current or present, preserve that meaning.
10. Do not infer missing dates or locations.
11. Extract technical and non-technical skills.
12. Extract tools and software explicitly mentioned.
    13. Extract education, formal training, and certifications from the CV.
    14. Classify an item as education when it represents a degree, diploma,
        academic program, or formal educational/training program.
    15. Classify an item as a certification only when the CV explicitly
        presents it as a certification, certificate, or credential.
    16. Do not turn individual subjects, skills, courses, or technologies
        into separate certifications unless the CV explicitly identifies
        each one as a certification or credential.
    17. Identify industries represented by the candidate's experience.
    18. Identify transferable skills only when they are reasonably supported
        by evidence in the CV.
    19. Extract URLs and links that are explicitly present in the CV.
    20. Associate each link with the specific experience or project where
    the link appears.
    21. Preserve the exact link label used in the CV whenever a label is
    explicitly present.
    22. If the CV explicitly says "Live Demo", use "Live Demo", not
    "Demo", "Remote Demo", or another variation.
    23. If the CV explicitly says "API Docs", use "API Docs" for that link.
    24. Do not invent, improve, normalize, or reinterpret a link label.
    25. If a URL is present without a nearby explicit label, use a simple
    factual label such as "Link" rather than inventing a description.
    26. Do not invent URLs.
    27. Do not move a link from one experience or project to another.
    28. Record useful evidence in evidence_notes.
    29. Preserve experience dates and locations exactly when they are explicitly
    supported by the CV.
    30. Do not invent employers, dates, technologies, metrics, achievements,
    certifications, locations, or responsibilities.
    31. Do not upgrade a claim from "familiar with" to "experienced in".
    32. Do not turn an implied possibility into a factual achievement.
    33. Keep the analysis faithful to the source CV.
    34. Do not assign a link to a project or experience solely because the
        link appears later in the extracted CV text.
    35. Associate a link with a project or experience only when the supplied
        CV text provides reliable evidence for that association.
    36. PDF text extraction may reorder headings, descriptions, and links.
        Treat link ownership as ambiguous when the extracted text does not
        provide reliable evidence of ownership.
    37. When link ownership is ambiguous, leave the link unassigned rather
        than attaching it to the nearest project or experience.
    38. Record ambiguous link ownership in evidence_notes when useful.
"""

    def __init__(self, provider: GeminiProvider | None = None):
        self.provider = provider or GeminiProvider()

    async def analyze(self, *, cv_text: str) -> CVAnalysis:
        """Analyze CV text and return structured candidate information."""

        cleaned_cv = cv_text.strip()

        if not cleaned_cv:
            raise ValueError("CV content is required.")

        user_prompt = f"""
Analyze the following CV.

CV CONTENT:
{cleaned_cv}
"""

        result = await self.provider.generate_structured(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=CVAnalysis,
        )
        return cast(CVAnalysis, result)
