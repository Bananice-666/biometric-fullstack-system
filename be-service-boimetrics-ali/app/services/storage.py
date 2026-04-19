from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Protocol
from uuid import uuid4

from pymongo import ASCENDING, MongoClient  # pyright: ignore[reportMissingImports]

from app.config import MONGODB_COLLECTION_NAME, MONGODB_DB_NAME, MONGODB_URI
from app.services.face_engine import FacePoint


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


@dataclass
class TemplateRecord:
    template_id: str
    vector: List[float]
    face_points: List[FacePoint]
    created_at: datetime


@dataclass
class SubjectRecord:
    subject_id: str
    enrolled_at: datetime
    updated_at: datetime
    templates: List[TemplateRecord] = field(default_factory=list)


class BaseFaceRegistry(Protocol):
    def list_subjects(self) -> List[SubjectRecord]:
        ...

    def get_subject(self, subject_id: str) -> Optional[SubjectRecord]:
        ...

    def add_template(self, subject_id: str, vector: List[float], face_points: List[FacePoint]) -> TemplateRecord:
        ...

    def delete_subject(self, subject_id: str) -> bool:
        ...


class InMemoryFaceRegistry:
    def __init__(self) -> None:
        self._subjects: Dict[str, SubjectRecord] = {}

    def list_subjects(self) -> List[SubjectRecord]:
        return [self._clone_subject(subject) for subject in self._subjects.values()]

    def get_subject(self, subject_id: str) -> Optional[SubjectRecord]:
        subject = self._subjects.get(subject_id)
        if subject is None:
            return None
        return self._clone_subject(subject)

    def add_template(self, subject_id: str, vector: List[float], face_points: List[FacePoint]) -> TemplateRecord:
        now = utc_now()
        subject = self._subjects.get(subject_id)
        if subject is None:
            subject = SubjectRecord(subject_id=subject_id, enrolled_at=now, updated_at=now)
            self._subjects[subject_id] = subject

        template = TemplateRecord(
            template_id=f"tmpl-{uuid4().hex[:12]}",
            vector=list(vector),
            face_points=list(face_points),
            created_at=now,
        )
        subject.templates.append(template)
        subject.updated_at = now
        return self._clone_template(template)

    def delete_subject(self, subject_id: str) -> bool:
        return self._subjects.pop(subject_id, None) is not None

    def _clone_template(self, template: TemplateRecord) -> TemplateRecord:
        return TemplateRecord(
            template_id=template.template_id,
            vector=list(template.vector),
            face_points=[FacePoint(x=point.x, y=point.y, intensity=point.intensity) for point in template.face_points],
            created_at=template.created_at,
        )

    def _clone_subject(self, subject: SubjectRecord) -> SubjectRecord:
        return SubjectRecord(
            subject_id=subject.subject_id,
            enrolled_at=subject.enrolled_at,
            updated_at=subject.updated_at,
            templates=[self._clone_template(template) for template in subject.templates],
        )


class MongoFaceRegistry:
    def __init__(
        self,
        mongodb_uri: str = MONGODB_URI,
        database_name: str = MONGODB_DB_NAME,
        collection_name: str = MONGODB_COLLECTION_NAME,
    ) -> None:
        if not mongodb_uri:
            raise ValueError("MONGODB_URI is required to use MongoFaceRegistry.")

        self.client = MongoClient(mongodb_uri)
        self.collection = self.client[database_name][collection_name]
        self.collection.create_index([("subject_id", ASCENDING)], unique=True)

    def list_subjects(self) -> List[SubjectRecord]:
        return [self._document_to_subject(document) for document in self.collection.find({})]

    def get_subject(self, subject_id: str) -> Optional[SubjectRecord]:
        document = self.collection.find_one({"subject_id": subject_id})
        if document is None:
            return None
        return self._document_to_subject(document)

    def add_template(self, subject_id: str, vector: List[float], face_points: List[FacePoint]) -> TemplateRecord:
        now = utc_now()
        template = TemplateRecord(
            template_id=f"tmpl-{uuid4().hex[:12]}",
            vector=list(vector),
            face_points=list(face_points),
            created_at=now,
        )

        template_document = self._template_to_document(template)
        self.collection.update_one(
            {"subject_id": subject_id},
            {
                "$setOnInsert": {
                    "subject_id": subject_id,
                    "enrolled_at": now,
                },
                "$set": {"updated_at": now},
                "$push": {"templates": template_document},
            },
            upsert=True,
        )
        return template

    def delete_subject(self, subject_id: str) -> bool:
        result = self.collection.delete_one({"subject_id": subject_id})
        return result.deleted_count > 0

    def _template_to_document(self, template: TemplateRecord) -> dict:
        return {
            "template_id": template.template_id,
            "vector": list(template.vector),
            "face_points": [
                {"x": point.x, "y": point.y, "intensity": point.intensity}
                for point in template.face_points
            ],
            "created_at": to_iso(template.created_at),
        }

    def _document_to_template(self, document: dict) -> TemplateRecord:
        return TemplateRecord(
            template_id=document["template_id"],
            vector=list(document.get("vector", [])),
            face_points=[
                FacePoint(x=point["x"], y=point["y"], intensity=point["intensity"])
                for point in document.get("face_points", [])
            ],
            created_at=from_iso(document["created_at"]),
        )

    def _document_to_subject(self, document: dict) -> SubjectRecord:
        templates = [self._document_to_template(template) for template in document.get("templates", [])]
        return SubjectRecord(
            subject_id=document["subject_id"],
            enrolled_at=document.get("enrolled_at", utc_now()),
            updated_at=document.get("updated_at", utc_now()),
            templates=templates,
        )
