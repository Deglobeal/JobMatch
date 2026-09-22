"""Main FastAPI application for the JobMatch API."""

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

job_search_service = JobSearchService()
job_match_service = JobMatchService()
cv_extractor = CVExtractor()
cv_profile_extractor = CVProfileExtractor()

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


