"""JobMatch Agent 3: Matching & Improvement Agent."""

from app.ai.gemini_provider import GeminiProvider
from app.agents.matching_agent import MatchingAnalysis


class MatchingAnalyzer:
    """Compare job requirements with CV evidence using the AI provider."""

    SYSTEM_PROMPT = """
You are JobMatch Agent 3, the Matching & Improvement Agent.

Your task is to compare a structured job-description analysis with a
structured CV analysis and produce a factual matching analysis.

Rules:

1. Use ONLY the supplied job-analysis and CV-analysis data.
2. Do not invent qualifications, experience, achievements, technologies,
   employers, certifications, or responsibilities.
3. Treat the CV analysis as the source of truth for candidate evidence.
4. A requirement is a strong match only when the CV contains clear
   supporting evidence.
5. A requirement is a partial match when the CV provides related but
   incomplete evidence.
6. Put unsupported requirements in missing_or_unclear.
7. Do not treat reading about, knowing about, or being interested in a
   technology as professional experience with that technology.
8. Do not upgrade "familiarity" or "exposure" into hands-on experience.
9. Transferable experience may be identified only when supported by the
   CV evidence.
10. CV improvements must use existing evidence. They may improve wording,
    emphasis, ordering, or clarity, but must not add new facts.
11. Suggested rewrites must remain truthful to the supplied CV.
12. Keywords_to_consider may include relevant job keywords that are
    supported by the candidate's evidence.
13. If a job keyword is not supported by the CV, do not recommend inserting
    it as though the candidate has that skill.
14. truth_warnings must identify any important limitation, unsupported
    claim, or potential misrepresentation risk.
15. should_tailor_cv should be true when meaningful evidence-based
    improvements could improve alignment with the job.
16. tailoring_priority should list the most important evidence-based
    changes first.
17. match_percentage must reflect the supplied evidence and requirements.
18. Do not give career advice unrelated to the supplied job and CV.
19. Keep the assessment concise, factual, and evidence-grounded.
20. For every item in cv_improvements, current_evidence MUST be copied
    verbatim from the ORIGINAL CV TEXT supplied in the user prompt.
21. current_evidence MUST be an exact contiguous substring of the original
    CV text. Do not paraphrase, summarize, normalize, or shorten it.
22. Never use ellipses ("...") or truncation in current_evidence.
23. suggested_change MUST be the actual replacement CV wording that can
    replace current_evidence directly. Do not write instructions such as
    "Highlight X", "Emphasize Y", or "Mention Z".
24. suggested_change may only use facts explicitly supported by the original
    CV text or supplied CV analysis.
25. If an improvement cannot be expressed as a safe replacement using exact
    original CV evidence, omit that improvement rather than inventing or
    paraphrasing evidence.
"""

    def __init__(self, provider: GeminiProvider | None = None):
        self.provider = provider or GeminiProvider()

    async def analyze(
        self,
        *,
        job_analysis: dict,
        cv_analysis: dict,
        original_cv_text: str,
        deterministic_match: dict | None = None,
    ) -> MatchingAnalysis:
        """Compare job requirements with CV evidence."""

        if not job_analysis:
            raise ValueError("Job analysis is required.")

        if not cv_analysis:
            raise ValueError("CV analysis is required.")

        print(
            "AGENT3 INPUT SIZES:",
            {
                "job_analysis_chars": len(str(job_analysis)),
                "cv_analysis_chars": len(str(cv_analysis)),
                "original_cv_text_chars": len(original_cv_text),
                "deterministic_match_chars": len(str(deterministic_match or "Not provided")),
            },
        )

        user_prompt = f"""
Compare the following job analysis with the following CV analysis.

JOB ANALYSIS:
{job_analysis}

CV ANALYSIS:
{cv_analysis}

ORIGINAL CV TEXT:
{original_cv_text}

DETERMINISTIC MATCH RESULT:
{deterministic_match or "Not provided"}

Produce the structured matching analysis.

Remember:
- Candidate evidence must come from the CV analysis and original CV.
- Do not invent experience.
- Do not turn exposure into professional experience.
- CV improvements must be grounded in existing evidence.
- current_evidence must be copied exactly from ORIGINAL CV TEXT.
- Never use "..." or other truncation in current_evidence.
- suggested_change must be actual replacement CV wording, not an editing instruction.
"""

        return await self.provider.generate_structured(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=MatchingAnalysis,
        )
