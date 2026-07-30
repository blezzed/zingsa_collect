from django.core.management.base import BaseCommand

from apps.forms.models import Form
from apps.forms.services.question_schema import infer_geometry_type_from_questions


class Command(BaseCommand):
    help = (
        "Correct Form.geometry_type from spatial questions in the current schema "
        "(e.g. location/point/line/polygon when geometry_type was left as none)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show changes without saving.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        updated = 0
        unchanged = 0

        qs = Form.objects.select_related("current_version").all()
        for form in qs:
            version = form.current_version
            if not version or not isinstance(version.schema, dict):
                unchanged += 1
                continue

            inferred = infer_geometry_type_from_questions(
                version.schema.get("questions", [])
            )
            if inferred == form.geometry_type:
                unchanged += 1
                continue

            self.stdout.write(
                f"{form.id} | {form.title[:50]:50} | "
                f"{form.geometry_type} -> {inferred}"
            )

            if not dry_run:
                form.geometry_type = inferred
                schema = dict(version.schema)
                schema["geometryType"] = inferred
                version.schema = schema
                version.save(update_fields=["schema"])
                form.save(update_fields=["geometry_type", "updated_at"])
            updated += 1

        action = "Would update" if dry_run else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} {updated} form(s); {unchanged} already correct."
            )
        )
