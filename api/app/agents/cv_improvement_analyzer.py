"""JobMatch CV Improvement Agent."""

from app.ai.provider import AIProvider
from app.agents.cv_improvement_agent import CVImprovementPlan


class CVImprovementAnalyzer:
    """Generate safe, evidence-grounded CV improvement plans."""

    SYSTEM_PROMPT = """
You are the JobMatch CV Improvement Agent.

Your task is to identify specific, evidence-grounded improvements that can
be made to an editable CV to better align it with a target job description.

The candidate's CV is the source of truth.

Rules:

1. Use ONLY information supplied in the job analysis, CV analysis, current
   match analysis, and editable CV content.
2. Never invent employment, qualifications, certifications, skills,
   achievements, responsibilities, dates, employers, projects, or experience.
3. Never recommend adding a skill merely because it appears in the job
   description.
4. A missing requirement must remain missing unless the supplied CV
   contains genuine supporting evidence.
5. Improvements may:
   - rewrite existing wording,
   - make existing evidence clearer,
   - improve emphasis,
   - reorder or consolidate existing information,
   - make supported keywords more visible.
6. Improvements must not create new facts.
7. current_content must identify the existing editable CV content that is
   being improved.
8. proposed_content must be the actual replacement wording, not an
   instruction such as "highlight this skill".
9. evidence_used must contain only evidence actually present in the supplied
   CV analysis or editable CV content.
10. If there is no safe evidence-based improvement for a requirement, do not
    create an improvement for it.
11. potential_match represents the estimated alignment after applying ONLY
    the proposed safe improvements. It is not a guarantee.
12. Never inflate potential_match simply to reach 90% or 100%.
13. potential_match must not exceed 100.
14. current_match must equal the supplied current match percentage.
15. unsupported_requirements must identify important job requirements for
    which the supplied CV contains no sufficient evidence.
16. truth_warnings must identify any limitation or potential
    misrepresentation risk.
17. safe_to_apply_all must be true only when every proposed improvement is
    safe to apply without adding unsupported facts.
18. Keep improvements practical and specific enough for a CV editor to apply.
19. The CV may belong to any profession. Do not assume the candidate is a
    software developer or belongs to any particular industry.
20. Do not provide unrelated career advice.

Your output must be structured according to the supplied CVImprovementPlan
schema.
"""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    async def analyze(
        self,
        *,
        job_analysis: dict,
        cv_analysis: dict,
        matching_analysis: dict,
        editable_cv_content: dict | str,
    ) -> CVImprovementPlan:
        """Generate an evidence-grounded improvement plan."""

        if not job_analysis:
            raise ValueError("Job analysis is required.")

        if not cv_analysis:
            raise ValueError("CV analysis is required.")

        if not matching_analysis:
            raise ValueError("Matching analysis is required.")

        if not editable_cv_content:
            raise ValueError("Editable CV content is required.")

        current_match = matching_analysis.get(
            "match_percentage",
            0,
        )

        user_prompt = f"""
Create an evidence-grounded CV improvement plan.

TARGET JOB ANALYSIS:
{job_analysis}

CV ANALYSIS:
{cv_analysis}

CURRENT MATCH ANALYSIS:
{matching_analysis}

EDITABLE CV CONTENT:
{editable_cv_content}

CURRENT MATCH PERCENTAGE:
{current_match}

Identify the highest-value safe improvements that can be made to the
editable CV using existing evidence.

For each improvement:
- identify the CV section and field,
- explain why the change improves alignment,
- show the current content,
- provide the exact proposed replacement wording,
- identify the evidence supporting the replacement,
- describe the expected match impact,
- mark whether it is safe to apply.

Then estimate the potential match after applying only the safe proposed
changes.

Do not invent anything to increase the score.
Do not force the potential match toward 90% or 100%.
If important requirements remain unsupported, list them explicitly.
"""

        return await self.provider.generate_structured(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=CVImprovementPlan,
        )
