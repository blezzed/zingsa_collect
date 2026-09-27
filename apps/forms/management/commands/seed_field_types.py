from django.core.management.base import BaseCommand
from apps.forms.models import FormFieldType

CANONICAL = {
    "text",
    "textarea",
    "number",
    "date",
    "time",
    "datetime",
    "phone",
    "email",
    "url",
    "radio",
    "checkbox",
    "dropdown",
    "slider",
    "rating",
    "image",
    "video",
    "voice",
    "file",
    "signature",
    "location",
    "point",
    "line",
    "polygon",
    "collection",
    "calculated",
}


class Command(BaseCommand):
    help = "Seeds Form Field Types from the ZINGSA Collect question type specification"

    def handle(self, *args, **kwargs):
        types = [
            {
                "name": "text",
                "label": "Single-line text input",
                "category": "Basic",
                "schema": {
                    "minLength": "number",
                    "maxLength": "number",
                    "smartenable": "boolean",
                    "scanEnabled": "boolean",
                },
            },
            {
                "name": "textarea",
                "label": "Multi-line text input",
                "category": "Basic",
                "schema": {
                    "minLength": "number",
                    "maxLength": "number",
                    "smartenable": "boolean",
                    "scanEnabled": "boolean",
                },
            },
            {
                "name": "number",
                "label": "Numeric input",
                "category": "Basic",
                "schema": {
                    "min": "number",
                    "max": "number",
                    "numericType": "string",
                    "decimalPlaces": "number",
                    "smartenable": "boolean",
                    "scanEnabled": "boolean",
                },
            },
            {
                "name": "email",
                "label": "Email input",
                "category": "Basic",
                "schema": {"smartenable": "boolean"},
            },
            {
                "name": "phone",
                "label": "Phone number input",
                "category": "Basic",
                "schema": {"smartenable": "boolean", "scanEnabled": "boolean"},
            },
            {
                "name": "url",
                "label": "URL input",
                "category": "Basic",
                "schema": {"smartenable": "boolean", "scanEnabled": "boolean"},
            },
            {
                "name": "date",
                "label": "Date picker",
                "category": "Date & Time",
                "schema": {"autocapture": "boolean"},
            },
            {
                "name": "time",
                "label": "Time picker",
                "category": "Date & Time",
                "schema": {"autocapture": "boolean"},
            },
            {
                "name": "datetime",
                "label": "Date and time picker",
                "category": "Date & Time",
                "schema": {"autocapture": "boolean"},
            },
            {
                "name": "radio",
                "label": "Single-choice selection",
                "category": "Selection",
                "schema": {"options": [{"label": "string", "value": "string"}]},
            },
            {
                "name": "checkbox",
                "label": "Multiple-choice selection",
                "category": "Selection",
                "schema": {
                    "options": [{"label": "string", "value": "string"}],
                    "multiselect": "boolean",
                    "minSelections": "number",
                    "maxSelections": "number",
                },
            },
            {
                "name": "dropdown",
                "label": "Dropdown selection",
                "category": "Selection",
                "schema": {
                    "options": [{"label": "string", "value": "string"}],
                    "multiselect": "boolean",
                    "minSelections": "number",
                    "maxSelections": "number",
                },
            },
            {
                "name": "slider",
                "label": "Slider input",
                "category": "Advanced",
                "schema": {"min": "number", "max": "number", "step": "number"},
            },
            {
                "name": "rating",
                "label": "Rating scale",
                "category": "Advanced",
                "schema": {"maxStars": "number"},
            },
            {
                "name": "image",
                "label": "Image/photo capture",
                "category": "Media",
                "schema": {"maxPhotos": "number", "noUpload": "boolean"},
            },
            {
                "name": "video",
                "label": "Video capture",
                "category": "Media",
                "schema": {"maxDuration": "number", "noUpload": "boolean"},
            },
            {
                "name": "voice",
                "label": "Voice recording",
                "category": "Media",
                "schema": {"maxDuration": "number"},
            },
            {
                "name": "file",
                "label": "Generic file upload",
                "category": "Media",
                "schema": {
                    "maxFiles": "number",
                    "allowedTypes": ["string"],
                },
            },
            {"name": "signature", "label": "Signature capture", "category": "Media", "schema": {}},
            {
                "name": "location",
                "label": "GPS location capture",
                "category": "Location & GIS",
                "schema": {"maxAccuracy": "number"},
            },
            {
                "name": "point",
                "label": "Map point capture",
                "category": "Location & GIS",
                "schema": {},
            },
            {"name": "line", "label": "GIS line capture", "category": "Location & GIS", "schema": {}},
            {
                "name": "polygon",
                "label": "GIS polygon capture",
                "category": "Location & GIS",
                "schema": {},
            },
            {
                "name": "collection",
                "label": "Repeating subform",
                "category": "Advanced",
                "schema": {"itemLabel": "string", "questions": "array"},
            },
            {
                "name": "calculated",
                "label": "Calculated field",
                "category": "Advanced",
                "schema": {"expression": "string"},
            },
            # Legacy / aliases (hidden from builder via is_active=False)
            {"name": "select", "label": "Dropdown selection", "category": "Selection", "schema": {}},
            {"name": "password", "label": "Password input", "category": "Basic", "schema": {}},
            {"name": "audio", "label": "Audio recording", "category": "Media", "schema": {}},
            {"name": "contact", "label": "Contact information", "category": "Device Data", "schema": {}},
            {"name": "barcode", "label": "Barcode scanner", "category": "Scanning", "schema": {}},
            {"name": "qr", "label": "QR scanner", "category": "Scanning", "schema": {}},
            {"name": "section", "label": "Section header", "category": "Layout", "schema": {}},
            {"name": "group", "label": "Question group", "category": "Layout", "schema": {}},
            {"name": "note", "label": "Read-only note", "category": "Layout", "schema": {}},
        ]

        created_count = 0
        for item in types:
            is_active = item["name"] in CANONICAL
            obj, created = FormFieldType.objects.get_or_create(
                name=item["name"],
                defaults={
                    "label": item["label"],
                    "category": item["category"],
                    "properties_schema": item.get("schema", {}),
                    "is_active": is_active,
                },
            )
            if created:
                created_count += 1
            else:
                obj.label = item["label"]
                obj.category = item["category"]
                obj.properties_schema = item.get("schema", {})
                obj.is_active = is_active
                obj.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded {len(types)} field types (Created: {created_count})."
            )
        )
