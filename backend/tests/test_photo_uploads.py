"""
Tests for Phase 6 Photo Uploads:
- Storage abstraction and local fallback
- Image validation, format checks, file size enforcement
- EXIF & GPS metadata stripping
- Report image upload and delete endpoints
- Ownership authorization and max 3 images limit
"""
from datetime import date
import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.services.image_service import ImageService, ImageValidationError
from app.services.auth_service import get_current_user
from app.models.report import Report, ReportImage, User
from app.database import get_db


def create_test_image(format="JPEG", size=(800, 600), color=(82, 124, 118), with_exif=False) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    if with_exif and format == "JPEG":
        exif = img.getexif()
        exif[0x010f] = "TestCameraManufacturer"
        exif[0x0110] = "TestCameraModel"
        img.save(buf, format=format, exif=exif)
    else:
        img.save(buf, format=format)
    return buf.getvalue()


def test_image_validation_valid_formats():
    for fmt in ["JPEG", "PNG", "WEBP"]:
        raw = create_test_image(format=fmt)
        main_bytes, thumb_bytes, path_main, path_thumb, mime = ImageService.validate_and_process_image(
            raw, f"test.{fmt.lower()}", f"image/{fmt.lower()}"
        )
        assert len(main_bytes) > 0
        assert len(thumb_bytes) > 0
        assert path_main.endswith(".webp")
        assert path_thumb.endswith("_thumb.webp")
        assert mime == "image/webp"


def test_image_validation_rejects_corrupt_file():
    with pytest.raises(ImageValidationError):
        ImageService.validate_and_process_image(
            b"this is not an image at all", "fake.jpg", "image/jpeg"
        )


def test_image_validation_rejects_unsupported_mime():
    raw = create_test_image(format="GIF")
    with pytest.raises(ImageValidationError):
        ImageService.validate_and_process_image(
            raw, "test.gif", "image/gif"
        )


def test_image_validation_rejects_oversized():
    # 6 MB of dummy bytes
    oversized = b"0" * (6 * 1024 * 1024)
    with pytest.raises(ImageValidationError, match="exceeds maximum"):
        ImageService.validate_and_process_image(
            oversized, "big.jpg", "image/jpeg"
        )


def test_exif_metadata_completely_stripped():
    raw_with_exif = create_test_image(format="JPEG", with_exif=True)
    # Check original has exif
    orig_img = Image.open(io.BytesIO(raw_with_exif))
    assert len(orig_img.getexif().keys()) > 0

    main_bytes, thumb_bytes, _, _, _ = ImageService.validate_and_process_image(
        raw_with_exif, "photo.jpg", "image/jpeg"
    )

    clean_img = Image.open(io.BytesIO(main_bytes))
    assert len(clean_img.getexif().keys()) == 0


def test_upload_image_endpoint_and_ownership(client: TestClient, db_session):
    # Setup test users
    owner = User(
        display_name="Owner User",
        email="owner_photo@example.com",
        password_hash="argon2id$mockhash",
        role="user",
    )
    stranger = User(
        display_name="Stranger User",
        email="stranger_photo@example.com",
        password_hash="argon2id$mockhash",
        role="user",
    )
    db_session.add_all([owner, stranger])
    db_session.commit()
    db_session.refresh(owner)
    db_session.refresh(stranger)

    # Create report owned by owner
    report = Report(
        type="LOST",
        item_name="Hydro Flask Teal",
        category="OTHER",
        description="Left near bench in quad.",
        event_date=date(2026, 10, 15),
        location_text="Admin Quad",
        normalized_location="admin quad",
        status="ACTIVE",
        owner_id=owner.id,
        contact_name="Owner User",
        contact_email="owner_photo@example.com",
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    # 1. Stranger tries to upload image -> 403 Forbidden
    app.dependency_overrides[get_current_user] = lambda: stranger
    img_data = create_test_image()
    files = {"file": ("test.jpg", img_data, "image/jpeg")}
    res = client.post(f"/api/reports/{report.id}/images", files=files)
    assert res.status_code == 403

    # 2. Owner uploads 1st image -> 201 Created
    app.dependency_overrides[get_current_user] = lambda: owner
    files = {"file": ("flask1.jpg", img_data, "image/jpeg")}
    res = client.post(f"/api/reports/{report.id}/images", files=files)
    assert res.status_code == 201
    img1_id = res.json()["data"]["id"]
    assert res.json()["data"]["image_url"] is not None

    # Verify report detail contains the image
    res_detail = client.get(f"/api/reports/{report.id}")
    assert res_detail.status_code == 200
    images = res_detail.json()["data"]["images"]
    assert len(images) == 1
    assert images[0]["id"] == img1_id

    # 3. Owner uploads 2nd and 3rd images
    for i in (2, 3):
        f = {"file": (f"flask{i}.jpg", img_data, "image/jpeg")}
        r = client.post(f"/api/reports/{report.id}/images", files=f)
        assert r.status_code == 201

    # 4. Owner tries to upload 4th image -> 400 Bad Request (Limit 3)
    f = {"file": ("flask4.jpg", img_data, "image/jpeg")}
    r = client.post(f"/api/reports/{report.id}/images", files=f)
    assert r.status_code == 400
    assert "Maximum 3 images" in r.json()["error"]["message"]

    # 5. Stranger tries to delete owner's image -> 403 Forbidden
    app.dependency_overrides[get_current_user] = lambda: stranger
    res_del_stranger = client.delete(f"/api/reports/{report.id}/images/{img1_id}")
    assert res_del_stranger.status_code == 403

    # 6. Owner deletes image -> 200 OK
    app.dependency_overrides[get_current_user] = lambda: owner
    res_del = client.delete(f"/api/reports/{report.id}/images/{img1_id}")
    assert res_del.status_code == 200

    # Verify image count is now 2
    res_detail2 = client.get(f"/api/reports/{report.id}")
    assert len(res_detail2.json()["data"]["images"]) == 2

    # Clean up override
    app.dependency_overrides.pop(get_current_user, None)
