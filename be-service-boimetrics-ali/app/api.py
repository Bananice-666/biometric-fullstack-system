from functools import lru_cache
from typing import Dict, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import DEFAULT_THRESHOLD, MONGODB_URI
from app.schemas import (
    IdentificationResponse,
    EnrollmentResponse,
    HealthResponse,
    SubjectDetail,
    SubjectSummary,
    VerificationResponse,
)
from app.services.biometric_service import BiometricService
from app.services.face_engine import FaceProcessingError
from app.services.storage import InMemoryFaceRegistry, MongoFaceRegistry


router = APIRouter(prefix="/api/v1", tags=["biometrics"])


@lru_cache(maxsize=1)
def get_service() -> BiometricService:
    if MONGODB_URI:
        return BiometricService(registry=MongoFaceRegistry())
    return BiometricService(registry=InMemoryFaceRegistry())


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="facial-biometrics-backend", version="1.0.0")


@router.post("/enroll", response_model=EnrollmentResponse)
async def enroll(
    subject_id: str = Form(...),
    image: UploadFile = File(...),
    service: BiometricService = Depends(get_service),
) -> EnrollmentResponse:
    image_bytes = await image.read()
    try:
        return service.enroll(subject_id=subject_id, image_bytes=image_bytes)
    except FaceProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/verify", response_model=VerificationResponse)
async def verify(
    subject_id: str = Form(...),
    image: UploadFile = File(...),
    threshold: float = Form(DEFAULT_THRESHOLD),
    service: BiometricService = Depends(get_service),
) -> VerificationResponse:
    image_bytes = await image.read()
    try:
        return service.verify(subject_id=subject_id, image_bytes=image_bytes, threshold=threshold)
    except FaceProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/identify", response_model=IdentificationResponse)
async def identify(
    image: UploadFile = File(...),
    threshold: float = Form(DEFAULT_THRESHOLD),
    service: BiometricService = Depends(get_service),
) -> IdentificationResponse:
    image_bytes = await image.read()
    try:
        return service.identify(image_bytes=image_bytes, threshold=threshold)
    except FaceProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/subjects", response_model=List[SubjectSummary])
def list_subjects(service: BiometricService = Depends(get_service)) -> List[SubjectSummary]:
    return service.list_subjects()


@router.get("/subjects/{subject_id}", response_model=SubjectDetail)
def get_subject(subject_id: str, service: BiometricService = Depends(get_service)) -> SubjectDetail:
    try:
        return service.get_subject(subject_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/subjects/{subject_id}")
def delete_subject(subject_id: str, service: BiometricService = Depends(get_service)) -> Dict[str, bool]:
    deleted = service.delete_subject(subject_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Unknown subject_id '{subject_id}'.")
    return {"deleted": True}
