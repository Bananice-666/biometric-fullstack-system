from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import List

import numpy as np
from PIL import Image, ImageOps


@dataclass(frozen=True)
class FacePoint:
    x: float
    y: float
    intensity: float


@dataclass(frozen=True)
class FaceEmbedding:
    vector: List[float]
    face_points: List[FacePoint]
    image_width: int
    image_height: int


class FaceProcessingError(ValueError):
    pass


class FaceEngine:
    """Lightweight biometric feature extractor.

    The current implementation is intentionally simple so the service works
    without large ML weights. The API is designed so the extractor can be
    replaced later by a production face embedding model.
    """

    def extract_embedding(self, image_bytes: bytes) -> FaceEmbedding:
        image = self._load_image(image_bytes)
        cropped = self._center_crop_square(image)
        resized = cropped.resize((64, 64))
        grayscale = ImageOps.grayscale(resized)
        normalized = np.asarray(grayscale, dtype=np.float32) / 255.0
        flattened = normalized.reshape(-1)
        face_points = self._sample_face_points(normalized)
        vector = self._normalize_vector(flattened)
        return FaceEmbedding(
            vector=vector.tolist(),
            face_points=face_points,
            image_width=image.width,
            image_height=image.height,
        )

    def similarity(self, vector_a: List[float], vector_b: List[float]) -> float:
        first = np.asarray(vector_a, dtype=np.float32)
        second = np.asarray(vector_b, dtype=np.float32)
        if first.size != second.size:
            raise FaceProcessingError("Embedding sizes do not match.")

        first = self._normalize_vector(first)
        second = self._normalize_vector(second)
        similarity = float(np.dot(first, second))
        return max(0.0, min(1.0, similarity))

    def _load_image(self, image_bytes: bytes) -> Image.Image:
        try:
            image = Image.open(BytesIO(image_bytes))
            return ImageOps.exif_transpose(image).convert("RGB")
        except Exception as exc:  # pragma: no cover - pillow raises different subclasses
            raise FaceProcessingError("The uploaded file is not a valid image.") from exc

    def _center_crop_square(self, image: Image.Image) -> Image.Image:
        width, height = image.size
        if width == 0 or height == 0:
            raise FaceProcessingError("The uploaded image is empty.")

        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        return image.crop((left, top, left + side, top + side))

    def _normalize_vector(self, values: np.ndarray) -> np.ndarray:
        centered = values.astype(np.float32)
        centered = centered - np.mean(centered)
        norm = float(np.linalg.norm(centered))
        if norm == 0.0:
            return centered
        return centered / norm

    def _sample_face_points(self, normalized_image: np.ndarray) -> List[FacePoint]:
        points: List[FacePoint] = []
        height, width = normalized_image.shape
        grid_size = 8
        cell_width = width // grid_size
        cell_height = height // grid_size

        for row in range(grid_size):
            for column in range(grid_size):
                x = min(width - 1, column * cell_width + cell_width // 2)
                y = min(height - 1, row * cell_height + cell_height // 2)
                points.append(
                    FacePoint(
                        x=round(x / max(1, width - 1), 6),
                        y=round(y / max(1, height - 1), 6),
                        intensity=round(float(normalized_image[y, x]), 6),
                    )
                )

        return points
