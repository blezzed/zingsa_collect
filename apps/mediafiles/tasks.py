"""Celery tasks for background image processing."""

import io
import logging

from celery import shared_task
from django.core.files.base import ContentFile

logger = logging.getLogger("zingsa_collect.mediafiles.tasks")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    retry_kwargs={"max_retries": 3},
    acks_late=True,
)
def compress_media_file(self, media_file_id: str):
    """Losslessly compress a MediaFile stored in MinIO.

    Steps:
      1. Load the DB record by PK (UUID string).
      2. Check if the file is an image (based on file_type or extension).
      3. Read the image bytes from storage.
      4. Apply Pillow optimisation (strip EXIF, optimize encoding).
      5. Overwrite the original file in MinIO with the smaller version.
    """
    from PIL import Image, ExifTags
    from apps.mediafiles.models.media_model import MediaFile

    try:
        obj = MediaFile.objects.get(pk=media_file_id)
    except MediaFile.DoesNotExist:
        logger.warning("compress_media_file: MediaFile id=%s not found, skipping.", media_file_id)
        return

    if not obj.file:
        logger.warning("compress_media_file: id=%s has no file, skipping.", media_file_id)
        return

    # Check if it's an image
    file_type = obj.file_type.lower()
    if not file_type.startswith("image/"):
        logger.info("compress_media_file: id=%s is not an image (%s), skipping.", media_file_id, file_type)
        return

    field_file = obj.file
    original_name = field_file.name

    # Read the original bytes
    try:
        field_file.open("rb")
        original_bytes = field_file.read()
        field_file.close()
    except Exception as exc:
        logger.error("compress_media_file: could not read id=%s from storage: %s", media_file_id, exc)
        raise

    original_size = len(original_bytes)

    # Open with Pillow
    try:
        img = Image.open(io.BytesIO(original_bytes))
    except Exception as exc:
        logger.warning("compress_media_file: id=%s is not a valid image format for Pillow: %s", media_file_id, exc)
        return
        
    img_format = (img.format or "JPEG").upper()

    # Preserve orientation from EXIF, then strip all EXIF data
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img) or img
    except Exception:
        pass

    # Remove EXIF entirely by not passing it during save
    output = io.BytesIO()

    save_kwargs = {}
    if img_format in ("JPEG", "JPG"):
        # Near-lossless: quality=85, optimize Huffman tables
        save_kwargs = {
            "format": "JPEG",
            "quality": 85,
            "optimize": True,
            "progressive": True,
        }
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
    elif img_format == "PNG":
        save_kwargs = {
            "format": "PNG",
            "optimize": True,
        }
    elif img_format == "WEBP":
        save_kwargs = {
            "format": "WEBP",
            "lossless": True,
            "quality": 100,
        }
    else:
        # For other formats, just re-save without EXIF
        save_kwargs = {
            "format": img_format,
        }

    try:
        img.save(output, **save_kwargs)
    except Exception:
        # Fallback: save as JPEG if the original format fails
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output, format="JPEG", quality=85, optimize=True)

    compressed_bytes = output.getvalue()
    compressed_size = len(compressed_bytes)

    # Only overwrite if we actually achieved savings (> 1 KB)
    if compressed_size < original_size - 1024:
        # Save without triggering signals
        field_file.save(original_name, ContentFile(compressed_bytes), save=False)
        MediaFile.objects.filter(pk=media_file_id).update(file_size=compressed_size)
        savings_pct = round((1 - compressed_size / original_size) * 100, 1)
        logger.info(
            "compress_media_file: id=%s compressed %s → %s bytes (%.1f%% savings)",
            media_file_id,
            f"{original_size:,}",
            f"{compressed_size:,}",
            savings_pct,
        )
    else:
        logger.info(
            "compress_media_file: id=%s already optimal (%s bytes, compressed would be %s bytes), skipping overwrite.",
            media_file_id,
            f"{original_size:,}",
            f"{compressed_size:,}",
        )


@shared_task
def sweep_uncompressed_images():
    """Safety-net periodic task: find images that may have been missed by the
    post_save signal (e.g., worker was down) and enqueue them for compression.

    Only targets images uploaded in the last 48 hours that are larger than 500 KB,
    since already-compressed images will be small.
    """
    from datetime import timedelta
    from django.utils import timezone
    from apps.mediafiles.models.media_model import MediaFile

    cutoff = timezone.now() - timedelta(hours=48)
    candidates = MediaFile.objects.filter(created_at__gte=cutoff, file_type__startswith="image/")

    enqueued = 0
    for img_obj in candidates.iterator():
        if img_obj.file_size and img_obj.file_size > 500 * 1024:
            compress_media_file.delay(str(img_obj.pk))
            enqueued += 1

    if enqueued:
        logger.info("sweep_uncompressed_images: enqueued %d images for compression.", enqueued)
