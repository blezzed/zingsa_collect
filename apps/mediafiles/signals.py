"""Django signals for the mediafiles app."""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.mediafiles.models.media_model import MediaFile

logger = logging.getLogger("zingsa_collect.mediafiles.signals")


@receiver(post_save, sender=MediaFile)
def enqueue_image_compression(sender, instance, created, **kwargs):
    """Enqueue a Celery task to compress a newly uploaded media file.

    Only fires on *creation* to avoid infinite loops.
    """
    if not created:
        return

    if not instance.file:
        return
        
    file_type = (instance.file_type or "").lower()
    if not file_type.startswith("image/"):
        return

    # Import here to avoid circular imports at module load time
    from apps.mediafiles.tasks import compress_media_file

    logger.info(
        "enqueue_image_compression: scheduling compression for MediaFile id=%s",
        instance.pk,
    )
    compress_media_file.delay(str(instance.pk))
