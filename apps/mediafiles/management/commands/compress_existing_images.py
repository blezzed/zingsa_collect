"""Management command to compress all existing images in zingsa_collect."""

from django.core.management.base import BaseCommand
from apps.mediafiles.tasks import compress_media_file
from apps.mediafiles.models.media_model import MediaFile

class Command(BaseCommand):
    help = "Compresses all existing MediaFile images stored in MinIO."

    def handle(self, *args, **options):
        # Filter for images based on file_type prefix
        images = MediaFile.objects.filter(file_type__startswith="image/")
        total = images.count()
        self.stdout.write(f"Found {total} images. Dispatching compression tasks...")

        enqueued = 0
        for image in images:
            # We delay the task to run in the background via Celery
            compress_media_file.delay(str(image.pk))
            enqueued += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully enqueued {enqueued} compression tasks."))
