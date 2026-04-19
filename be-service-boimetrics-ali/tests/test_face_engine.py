from io import BytesIO

from PIL import Image, ImageDraw

from app.services.biometric_service import BiometricService
from app.services.face_engine import FaceEngine
from app.services.storage import InMemoryFaceRegistry


def create_image_bytes(seed: int) -> bytes:
    image = Image.new("RGB", (128, 128), (seed, seed, seed))
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 112, 112), outline=(255 - seed, 40 + seed // 2, seed), width=4)
    draw.line((0, 0, 127, 127), fill=(seed, 255 - seed, 80), width=3)
    draw.line((0, 127, 127, 0), fill=(80, seed, 255 - seed), width=3)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_engine_extracts_embedding():
    engine = FaceEngine()
    embedding = engine.extract_embedding(create_image_bytes(120))

    assert len(embedding.vector) == 64 * 64
    assert len(embedding.face_points) == 64
    assert embedding.image_width == 128
    assert embedding.image_height == 128


def test_enroll_and_verify_same_image():
    service = BiometricService(registry=InMemoryFaceRegistry())
    image = create_image_bytes(100)

    enrolled = service.enroll("person-1", image)
    verified = service.verify("person-1", image, threshold=0.90)

    assert enrolled.subject_id == "person-1"
    assert enrolled.face_points_count == 64
    assert verified.verified is True
    assert verified.similarity >= 0.90


def test_identify_returns_best_match():
    service = BiometricService(registry=InMemoryFaceRegistry())
    first = create_image_bytes(80)
    second = create_image_bytes(180)

    service.enroll("subject-a", first)
    service.enroll("subject-b", second)

    result = service.identify(first, threshold=0.80)

    assert result.matched is True
    assert result.best_match is not None
    assert result.best_match.subject_id == "subject-a"
