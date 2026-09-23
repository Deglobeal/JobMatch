"""Assemble a structured CV document from deterministic and AI analysis."""

from app.agents.cv_agent import CVAnalysis
from app.services.cv_document import (
    CVDocument,
    CVExperienceDocument,
    CVLink,
    CVPersonalDetails,
    CVProjectDocument,
)
from app.services.cv_document_parser import CVDocumentParser


class CVDocumentAssembler:
    """Combine deterministic CV metadata with semantic Agent 2 analysis."""

    def __init__(self, parser: CVDocumentParser | None = None):
        self.parser = parser or CVDocumentParser()

    def assemble(
        self,
        *,
        cv_text: str,
        analysis: CVAnalysis,
    ) -> CVDocument:
        """Build a structured CV document without inventing source data."""

        parsed = self.parser.parse(cv_text)

        experience = [
            CVExperienceDocument(
                organization=item.organization,
                role=item.role,
                location=item.location,
                start_date=item.start_date,
                end_date=item.end_date,
                links=[
                    CVLink(label=link.label, url=link.url)
                    for link in item.links
                ],
                bullets=[
                    *item.responsibilities,
                    *item.achievements,
                ],
            )
            for item in analysis.experiences
        ]

        projects = [
            CVProjectDocument(
                name=item.name,
                description=item.description,
                technologies=list(item.technologies),
                links=[
                    CVLink(label=link.label, url=link.url)
                    for link in item.links
                ],
                bullets=list(item.bullets),
            )
            for item in analysis.projects
        ]

        return CVDocument(
            personal=parsed.personal,
            summary=analysis.professional_summary,
            experience=experience,
            projects=projects,
            education=list(analysis.education),
            certifications=list(analysis.certifications),
            skills=list(analysis.skills),
            source_text=parsed.source_text,
        )
