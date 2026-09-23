"""JobMatch Truth Checker: validate proposed CV changes against source evidence."""

from app.ai.gemini_provider import GeminiProvider
from app.agents.truth_checker import TruthCheckResult


class TruthChecker:
    """Validate AI-generated CV suggestions against the original CV."""

    SYSTEM_PROMPT = """
You are the JobMatch Truth Checker.

Your task is to determine whether proposed CV changes are supported by
the candidate's ORIGINAL CV content.

This is a factual verification task, not a rewriting task.

Rules:

1. The original CV is the primary source of truth.
2. A suggestion may be APPROVED only when the original CV contains clear
   evidence supporting the factual claim.
3. A suggestion must be REJECTED when it introduces a fact that is not
   supported by the original CV.
4. Do not infer professional experience from interest, reading, courses,
   exposure, familiarity, or vague mentions.
5. Do not convert a project into professional employment experience.
6. Do not increase the candidate's years of experience unless the original
   CV explicitly supports the duration.
7. Do not invent employers, job titles, responsibilities, technologies,
   certifications, metrics, achievements, deployments, clients, or results.
8. If a suggestion changes wording but preserves the factual meaning of the
   original CV, it may be approved.
9. If a suggestion combines multiple facts, every important factual claim
   must be supported before approving it.
10. When evidence exists, quote or closely identify the relevant CV evidence
    in the evidence field.
11. When evidence does not exist, evidence should be null or clearly state
    that no supporting evidence was found.
12. Use status="approved" only for supported suggestions.
13. Use status="rejected" for unsupported or misleading suggestions.
14. Use warnings for borderline cases that require human review.
15. all_suggestions_safe must be true only when every supplied suggestion is
    approved and none requires a warning.
16. Never create new CV content yourself. Only validate the supplied
    suggestions.
"""

    def __init__(self, provider: GeminiProvider | None = None):
        self.provider = provider or GeminiProvider()

    async def check(
        self,
        *,
        original_cv: str,
        suggestions: list[str],
    ) -> TruthCheckResult:
        """Validate proposed CV changes against the original CV."""

        cleaned_cv = original_cv.strip()

        if not cleaned_cv:
            raise ValueError("Original CV content is required.")

        if not suggestions:
            raise ValueError("At least one suggestion is required.")

        user_prompt = f"""
Validate the following proposed CV changes against the ORIGINAL CV.

ORIGINAL CV:
{cleaned_cv}

PROPOSED CV CHANGES:
{suggestions}

For each suggestion:
- determine whether the factual claim is supported;
- approve only when supported by the original CV;
- reject unsupported or misleading claims;
- provide the supporting CV evidence when available;
- explain the reason for the decision.

Do not rewrite the suggestions.
"""

        return await self.provider.generate_structured(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=TruthCheckResult,
        )
