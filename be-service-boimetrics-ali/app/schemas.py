from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class EnrollmentResponse(BaseModel):
    subject_id: str
    template_id: str
    similarity_baseline: float
    feature_vector_size: int
    face_points_count: int
    enrolled_at: datetime
    samples: int


class VerificationResponse(BaseModel):
    subject_id: str
    verified: bool
    similarity: float
    threshold: float
    matched_template_id: Optional[str] = None
    checked_at: datetime


class IdentificationMatch(BaseModel):
    subject_id: str
    template_id: str
    similarity: float


class IdentificationResponse(BaseModel):
    matched: bool
    threshold: float
    checked_at: datetime
    best_match: Optional[IdentificationMatch] = None


class SubjectSummary(BaseModel):
    subject_id: str
    enrolled_at: datetime
    samples: int
    updated_at: datetime


class SubjectDetail(SubjectSummary):
    template_ids: List[str] = Field(default_factory=list)
    template_count: int = 0
