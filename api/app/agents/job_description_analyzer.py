"""JobMatch Agent 1: Job Description Analyst."""

from app.ai.gemini_provider import GeminiProvider
from app.agents.job_description_agent import JobDescriptionAnalysis


class JobDescriptionAnalyzer:
    """Analyze a job description using the configured AI provider."""

    SYSTEM_PROMPT = """
You are JobMatch Agent 1, a Job Description Analyst.

Your task is to analyze a job description objectively and extract its
requirements into the provided structured schema.

Rules:
1. Analyze only the supplied job description.
2. Do not infer candidate qualifications or experience.
3. Separate required qualifications from preferred qualifications.
4. Mark a requirement as explicit=true only when the job description
   explicitly states it.
5. Use concise, factual wording.
6. Identify responsibilities separately from qualifications.
7. Extract technical and non-technical skills.
8. Extract experience, education, and certification requirements.
9. Extract useful job-search and CV-tailoring keywords.
10. Identify the industry or domain context when it is reasonably clear.
11. Put unclear, contradictory, vague, or ambiguous requirements in
    ambiguous_requirements.
12. Do not invent requirements that are not supported by the job description.
13. If the job title is supplied separately, use it as job_title.
14. If no job title is supplied and one is clearly stated in the job
    description, extract it.
15. If no job title can be established, leave job_title as null.
"""

    def __init__(self, provider: GeminiProvider | None = None):
        self.provider = provider or GeminiProvider()

    async def analyze(
        self,
        *,
        job_description: str,
        job_title: str | None = None,
    ) -> JobDescriptionAnalysis:
        """Analyze a job description and return structured requirements."""

        cleaned_description = job_description.strip()

        if not cleaned_description:
            raise ValueError("Job description is required.")

        title_context = (
            job_title.strip()
            if job_title and job_title.strip()
            else None
        )

        user_prompt = f"""
Analyze the following job description.

Job title supplied by the user:
{title_context or "Not supplied"}

Job description:
{cleaned_description}
"""

        return await self.provider.generate_structured(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=JobDescriptionAnalysis,
        )
