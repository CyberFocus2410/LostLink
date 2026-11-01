"""
Image processing, validation, EXIF stripping, and thumbnail generation service.
"""
import io
import uuid
from typing import Tuple
from PIL import Image, ImageOps, UnidentifiedImageError
from app.config import settings

ALLOWED_MIME_TYPES = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}

MAX_IMAGE_DIMENSION = 1200
THUMBNAIL_DIMENSION = 300


class ImageValidationError(Exception):
    pass


class ImageService:
    @staticmethod
    def validate_and_process_image(
        raw_bytes: bytes,
        original_filename: str,
        content_type: str,
    ) -> Tuple[bytes, bytes, str, str, str]:
        """
        Validates image size and content, strips EXIF/GPS metadata,
        and generates an optimized main image and thumbnail.

        Returns:
            (main_bytes, thumb_bytes, storage_path_main, storage_path_thumb, content_type)
        """
        # 1. Size validation
        if len(raw_bytes) > settings.STORAGE_MAX_FILE_SIZE_BYTES:
            max_mb = settings.STORAGE_MAX_FILE_SIZE_BYTES / (1024 * 1024)
            raise ImageValidationError(f"File size exceeds maximum allowed size of {max_mb:.0f} MB.")

        # 2. Content-type declaration check
        normalized_mime = content_type.lower().split(";")[0].strip()
        if normalized_mime not in ALLOWED_MIME_TYPES:
            raise ImageValidationError("Unsupported image format. Allowed formats: JPEG, PNG, WebP.")

        # 3. Magic bytes / true payload verification via Pillow
        try:
            img = Image.open(io.BytesIO(raw_bytes))
            img.verify()
        except (UnidentifiedImageError, Exception):
            raise ImageValidationError("Corrupt or invalid image file.")

        # Reopen after verify() (Pillow closes or invalidates the object after verify)
        img = Image.open(io.BytesIO(raw_bytes))

        if img.format not in ("JPEG", "PNG", "WEBP"):
            raise ImageValidationError(f"Invalid image format: {img.format}. Allowed: JPEG, PNG, WebP.")

        # 4. Transpose orientation based on EXIF before stripping metadata
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Ensure compatible mode for WebP encoding (RGB or RGBA)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in img.mode else "RGB")

        # 5. Process main optimized image (stripping EXIF metadata)
        main_img = img.copy()
        main_img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
        out_main = io.BytesIO()
        main_img.save(out_main, format="WEBP", quality=85)
        main_bytes = out_main.getvalue()

        # 6. Process thumbnail
        thumb_img = img.copy()
        thumb_img.thumbnail((THUMBNAIL_DIMENSION, THUMBNAIL_DIMENSION), Image.Resampling.LANCZOS)
        out_thumb = io.BytesIO()
        thumb_img.save(out_thumb, format="WEBP", quality=80)
        thumb_bytes = out_thumb.getvalue()

        # 7. Generate clean unique storage filenames
        file_id = uuid.uuid4().hex
        storage_path_main = f"reports/{file_id}.webp"
        storage_path_thumb = f"reports/{file_id}_thumb.webp"

        return main_bytes, thumb_bytes, storage_path_main, storage_path_thumb, "image/webp"

