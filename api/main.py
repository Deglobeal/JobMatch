"""Main FastAPI application for the JobMatch API."""

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agents.cv_analyzer import CVAnalyzer
from app.agents.cv_improvement_analyzer import CVImprovementAnalyzer
from app.ai.fallback_provider import FallbackAIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.groq_provider import GroqProvider
from app.ai.mistral_provider import MistralProvider
from app.ai.openai_provider import OpenAIProvider
from app.agents.job_description_analyzer import JobDescriptionAnalyzer
from app.agents.matching_analyzer import MatchingAnalyzer
from app.agents.truth_checker import TruthCheckResult
from app.agents.truth_checker_analyzer import TruthChecker
from app.services.cv_extractor import CVExtractor
from app.services.cv_profile import CVProfileExtractor
from app.services.job_match import JobMatchService
from app.services.job_search import JobSearchService


app = FastAPI(
    title="JobMatch API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://jobmatch-bice.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

job_search_service = JobSearchService()
job_match_service = JobMatchService()
cv_extractor = CVExtractor()
cv_profile_extractor = CVProfileExtractor()
ai_provider = FallbackAIProvider(
    providers=[
        OpenAIProvider(),
        GeminiProvider(),
        GroqProvider(),
        MistralProvider(),
    ]
)
job_description_analyzer = JobDescriptionAnalyzer(provider=ai_provider)
cv_analyzer = CVAnalyzer(provider=ai_provider)
matching_analyzer = MatchingAnalyzer(provider=ai_provider)
truth_checker = TruthChecker(provider=ai_provider)
cv_improvement_analyzer = CVImprovementAnalyzer(provider=ai_provider)


def _cv_analysis_to_match_profile(cv_analysis: dict) -> dict:
    """Convert current structured CV analysis into the matcher's profile shape."""

    experiences = cv_analysis.get("experiences") or []
    projects = cv_analysis.get("projects") or []

    experience_parts = []
    for experience in experiences:
        if not isinstance(experience, dict):
            experience_parts.append(str(experience))
            continue

        for field in (
            "role",
            "organization",
            "location",
            "start_date",
            "end_date",
            "responsibilities",
            "achievements",
            "industry",
        ):
            value = experience.get(field)
            if value:
                experience_parts.append(str(value))

    project_parts = []
    for project in projects:
        if not isinstance(project, dict):
            project_parts.append(str(project))
            continue

        for field in (
            "name",
            "description",
            "technologies",
            "bullets",
        ):
            value = project.get(field)
            if value:
                project_parts.append(str(value))

    return {
        "target_role": " ".join(
            str(item)
            for item in (cv_analysis.get("likely_roles") or [])
        ),
        "summary": cv_analysis.get("professional_summary") or "",
        "skills": cv_analysis.get("skills") or [],
        "experience": " ".join(experience_parts),
        "projects": " ".join(project_parts),
        "education": cv_analysis.get("education") or [],
        "certifications": cv_analysis.get("certifications") or [],
    }


class JobSearchRequest(BaseModel):
    """Request model for job searches."""

    query: str
    location: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None


class JobAnalysisRequest(BaseModel):
    """Request model for CV-to-job analysis."""

    cv_profile: dict
    job_description: str
    job_title: str | None = None


class CVImprovementRequest(BaseModel):
    """Request model for evidence-grounded CV improvement."""

    job_analysis: dict
    cv_analysis: dict
    matching_analysis: dict
    editable_cv_content: dict | str


class CVReanalysisRequest(BaseModel):
    """Request model for re-analyzing the current edited CV."""

    job_analysis: dict
    cv_analysis: dict
    original_cv_text: str
    job_description: str
    job_title: str | None = None


@app.post("/api/cv/extract")
async def extract_cv(file: UploadFile = File(...)):
    """Upload a CV and return its extracted text."""

    file_bytes = await file.read()

    try:
        text = await cv_extractor.extract(
            filename=file.filename or "",
            content_type=file.content_type or "",
            file_bytes=file_bytes,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "text": text,
    }


@app.post("/api/cv/profile")
async def create_cv_profile(file: UploadFile = File(...)):
    """Upload a CV and return an editable job-search profile."""

    file_bytes = await file.read()

    try:
        text = await cv_extractor.extract(
            filename=file.filename or "",
            content_type=file.content_type or "",
            file_bytes=file_bytes,
        )

        profile = cv_profile_extractor.extract(text)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "filename": file.filename,
        "target_role": profile["target_role"],
        "summary": profile["summary"],
        "skills": profile["skills"],
        "experience": profile["experience"],
        "projects": profile["projects"],
        "education": profile["education"],
        "certifications": profile["certifications"],
        "search_query": profile["search_query"],
    }


@app.post("/api/cv/tailor")
async def tailor_cv(
    job_description: str = Form(...),
    job_title: str | None = Form(None),
    file: UploadFile = File(...),
):
    """Analyze a CV against a supplied job description for tailoring."""

    cleaned_job_description = job_description.strip()

    if not cleaned_job_description:
        raise HTTPException(
            status_code=400,
            detail="Job description is required.",
        )

    file_bytes = await file.read()

    try:
        # Extract the original CV text.
        cv_text = await cv_extractor.extract(
            filename=file.filename or "",
            content_type=file.content_type or "",
            file_bytes=file_bytes,
        )

        # Preserve the existing deterministic CV profile extraction.
        profile = cv_profile_extractor.extract(cv_text)

        # Agent 1: analyze the job description independently.
        job_analysis = await job_description_analyzer.analyze(
            job_description=cleaned_job_description,
            job_title=job_title,
        )

        # Agent 2: analyze the original CV independently.
        cv_analysis = await cv_analyzer.analyze(
            cv_text=cv_text,
        )

        # Existing deterministic matcher remains the scoring layer.
        deterministic_result = job_match_service.analyze(
            cv_profile=profile,
            job_description=cleaned_job_description,
            job_title=job_title,
        )

        deterministic_match = {
            "match_score": deterministic_result.match_score,
            "matched_requirements": (
                deterministic_result.matched_requirements
            ),
            "partial_matches": deterministic_result.partial_matches,
            "missing_requirements": (
                deterministic_result.missing_requirements
            ),
            "requirement_details": (
                deterministic_result.requirement_details
            ),
            "keywords": deterministic_result.keywords,
            "tailoring_suggestions": (
                deterministic_result.tailoring_suggestions
            ),
        }

        # Agent 3: synthesize the AI analyses with the deterministic result.
        matching_analysis = await matching_analyzer.analyze(
            job_analysis=job_analysis.model_dump(),
            cv_analysis=cv_analysis.model_dump(),
            original_cv_text=cv_text,
            deterministic_match=deterministic_match,
        )

        # Truth Checker: validate every concrete proposed CV change against
        # the original extracted CV before it can reach the editing workflow.
        proposed_suggestions = list(
            matching_analysis.suggested_rewrites
        )

        proposed_suggestions.extend(
            improvement.suggested_change
            for improvement in matching_analysis.cv_improvements
        )

        if proposed_suggestions:
            truth_check = await truth_checker.check(
                original_cv=cv_text,
                suggestions=proposed_suggestions,
            )
        else:
            truth_check = TruthCheckResult(
                approved_suggestions=[],
                rejected_suggestions=[],
                warnings=[],
                all_suggestions_safe=True,
            )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    return {
        "job_title": (
            job_title.strip()
            if job_title and job_title.strip()
            else job_analysis.job_title
        ),
        "job_description": cleaned_job_description,
        "original_cv_text": cv_text,
        "cv": {
            "filename": file.filename,
            "target_role": profile["target_role"],
            "summary": profile["summary"],
            "skills": profile["skills"],
            "experience": profile["experience"],
            "projects": profile["projects"],
            "education": profile["education"],
            "certifications": profile["certifications"],
            "search_query": profile["search_query"],
        },
        "job_analysis": job_analysis.model_dump(),
        "cv_analysis": cv_analysis.model_dump(),
        "deterministic_match": deterministic_match,
        "matching_analysis": matching_analysis.model_dump(),
        "truth_check": truth_check.model_dump(),
    }


@app.post("/api/cv/improve")
async def improve_cv(request: CVImprovementRequest):
    """Generate an evidence-grounded CV improvement plan."""

    try:
        improvement_plan = await cv_improvement_analyzer.analyze(
            job_analysis=request.job_analysis,
            cv_analysis=request.cv_analysis,
            matching_analysis=request.matching_analysis,
            editable_cv_content=request.editable_cv_content,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    return improvement_plan.model_dump()


@app.post("/api/cv/reanalyze")
async def reanalyze_cv(request: CVReanalysisRequest):
    """Re-analyze the current edited CV against the same job."""

    try:
        profile = _cv_analysis_to_match_profile(request.cv_analysis)

        deterministic_result = job_match_service.analyze(
            cv_profile=profile,
            job_description=request.job_description,
            job_title=request.job_title,
        )

        deterministic_match = {
            "match_score": deterministic_result.match_score,
            "matched_requirements": (
                deterministic_result.matched_requirements
            ),
            "partial_matches": deterministic_result.partial_matches,
            "missing_requirements": (
                deterministic_result.missing_requirements
            ),
            "requirement_details": (
                deterministic_result.requirement_details
            ),
            "keywords": deterministic_result.keywords,
            "tailoring_suggestions": (
                deterministic_result.tailoring_suggestions
            ),
        }

        matching_analysis = await matching_analyzer.analyze(
            job_analysis=request.job_analysis,
            cv_analysis=request.cv_analysis,
            original_cv_text=request.original_cv_text,
            deterministic_match=deterministic_match,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    return {
        "matching_analysis": matching_analysis.model_dump(),
        "deterministic_match": deterministic_match,
    }


@app.post("/api/jobs/analyze")
async def analyze_job(request: JobAnalysisRequest):
    """Analyze a job description against a CV profile."""

    result = job_match_service.analyze(
        cv_profile=request.cv_profile,
        job_description=request.job_description,
        job_title=request.job_title,
    )

    return {
        "match_score": result.match_score,
        "matched_requirements": result.matched_requirements,
        "partial_matches": result.partial_matches,
        "missing_requirements": result.missing_requirements,
        "requirement_details": result.requirement_details,
        "keywords": result.keywords,
        "tailoring_suggestions": result.tailoring_suggestions,
    }


@app.get("/health")
def health():
    """Return the health status of the API."""

    return {
        "status": "ok",
        "service": "jobmatch-api",
    }


@app.post("/api/jobs/search")
async def search_jobs(request: JobSearchRequest):
    """Search the web for jobs matching the supplied criteria."""

    results = await job_search_service.search(
        query=request.query,
        location=request.location,
        employment_type=request.employment_type,
        experience_level=request.experience_level,
    )

    return {
        "query": request.query,
        "location": request.location,
        "employment_type": request.employment_type,
        "experience_level": request.experience_level,
        "jobs": [
            {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "employment_type": job.employment_type,
                "description": job.description,
                "source": job.source,
                "url": job.url,
            }
            for job in results
            if job is not None
        ],
    }


