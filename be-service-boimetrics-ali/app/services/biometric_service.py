from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.config import DEFAULT_THRESHOLD
from app.schemas import (
    IdentificationMatch,
    IdentificationResponse,
    EnrollmentResponse,
    SubjectDetail,
    SubjectSummary,
    VerificationResponse,
)
from app.services.face_engine import FaceEngine
from app.services.storage import BaseFaceRegistry, InMemoryFaceRegistry, SubjectRecord, TemplateRecord, utc_now


@dataclass
class VerificationResult:
    similarity: float
    verified: bool
    template: Optional[TemplateRecord]


@dataclass
class IdentificationResult:
    similarity: float
    template: TemplateRecord


class BiometricService:
    def __init__(self, engine: Optional[FaceEngine] = None, registry: Optional[BaseFaceRegistry] = None) -> None:
        self.engine = engine or FaceEngine()
        self.registry = registry or InMemoryFaceRegistry()

    def enroll(self, subject_id: str, image_bytes: bytes) -> EnrollmentResponse:
        embedding = self.engine.extract_embedding(image_bytes)
        template = self.registry.add_template(subject_id, embedding.vector, embedding.face_points)
        current_subject = self.registry.get_subject(subject_id)
        samples = len(current_subject.templates) if current_subject is not None else 1
        return EnrollmentResponse(
            subject_id=subject_id,
            template_id=template.template_id,
            similarity_baseline=1.0,
            feature_vector_size=len(template.vector),
            face_points_count=len(template.face_points),
            enrolled_at=template.created_at,
            samples=samples,
        )

    def verify(
        self,
        subject_id: str,
        image_bytes: bytes,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> VerificationResponse:
        subject = self._require_subject(subject_id)
        embedding = self.engine.extract_embedding(image_bytes)
        result = self._match_against_subject(subject, embedding.vector, threshold)
        return VerificationResponse(
            subject_id=subject_id,
            verified=result.verified,
            similarity=result.similarity,
            threshold=threshold,
            matched_template_id=result.template.template_id if result.template else None,
            checked_at=utc_now(),
        )

    def identify(self, image_bytes: bytes, threshold: float = DEFAULT_THRESHOLD) -> IdentificationResponse:
        embedding = self.engine.extract_embedding(image_bytes)
        best_match = None

        for subject in self.registry.list_subjects():
            match = self._best_template_match(subject, embedding.vector)
            if match is None:
                continue

            if best_match is None or match.similarity > best_match.similarity:
                best_match = IdentificationMatch(
                    subject_id=subject.subject_id,
                    template_id=match.template.template_id,
                    similarity=match.similarity,
                )

        matched = best_match is not None and best_match.similarity >= threshold
        return IdentificationResponse(
            matched=matched,
            threshold=threshold,
            checked_at=utc_now(),
            best_match=best_match if matched else None,
        )

    def list_subjects(self) -> List[SubjectSummary]:
        subjects = self.registry.list_subjects()
        return [
            SubjectSummary(
                subject_id=subject.subject_id,
                enrolled_at=subject.enrolled_at,
                samples=len(subject.templates),
                updated_at=subject.updated_at,
            )
            for subject in subjects
        ]

    def get_subject(self, subject_id: str) -> SubjectDetail:
        subject = self._require_subject(subject_id)
        return SubjectDetail(
            subject_id=subject.subject_id,
            enrolled_at=subject.enrolled_at,
            updated_at=subject.updated_at,
            samples=len(subject.templates),
            template_ids=[template.template_id for template in subject.templates],
            template_count=len(subject.templates),
        )

    def delete_subject(self, subject_id: str) -> bool:
        return self.registry.delete_subject(subject_id)

    def _require_subject(self, subject_id: str) -> SubjectRecord:
        subject = self.registry.get_subject(subject_id)
        if subject is None:
            raise ValueError(f"Unknown subject_id '{subject_id}'.")
        return subject

    def _best_template_match(self, subject: SubjectRecord, vector: List[float]) -> Optional[IdentificationResult]:
        best_template = None
        best_similarity = -1.0

        for template in subject.templates:
            similarity = self.engine.similarity(template.vector, vector)
            if similarity > best_similarity:
                best_similarity = similarity
                best_template = template

        if best_template is None:
            return None

        return IdentificationResult(
            similarity=max(0.0, best_similarity),
            template=TemplateRecord(
                template_id=best_template.template_id,
                vector=best_template.vector,
                face_points=best_template.face_points,
                created_at=best_template.created_at,
            ),
        )

    def _match_against_subject(self, subject: SubjectRecord, vector: List[float], threshold: float) -> VerificationResult:
        best_template = None
        best_similarity = -1.0

        for template in subject.templates:
            similarity = self.engine.similarity(template.vector, vector)
            if similarity > best_similarity:
                best_similarity = similarity
                best_template = template

        verified = best_template is not None and best_similarity >= threshold
        return VerificationResult(
            similarity=max(0.0, best_similarity),
            verified=verified,
            template=best_template if verified else None,
        )
