from django.core.management.base import BaseCommand
from apps.forms.models import FormFieldType

class Command(BaseCommand):
    help = 'Seeds the database with default Form Field Types from the ZINGSA Collect documentation'

    def handle(self, *args, **kwargs):
        types = [
            # Basic
            {'name': 'text', 'label': 'Single-line text input', 'category': 'Basic', 'schema': {'minLength': 'number', 'maxLength': 'number', 'pattern': 'string'}},
            {'name': 'textarea', 'label': 'Multi-line text input', 'category': 'Basic', 'schema': {'minLength': 'number', 'maxLength': 'number'}},
            {'name': 'number', 'label': 'Numeric input', 'category': 'Basic', 'schema': {'min': 'number', 'max': 'number', 'numericType': 'string', 'decimalPlaces': 'number'}},
            {'name': 'password', 'label': 'Password input', 'category': 'Basic', 'schema': {'minLength': 'number', 'maxLength': 'number'}},

            # Date/Time
            {'name': 'date', 'label': 'Date picker', 'category': 'Date & Time', 'schema': {'minDate': 'string', 'maxDate': 'string'}},
            {'name': 'time', 'label': 'Time picker', 'category': 'Date & Time', 'schema': {}},

            # Selection
            {'name': 'radio', 'label': 'Single-choice selection', 'category': 'Selection', 'schema': {'options': [{'label': 'string', 'value': 'string'}]}},
            {'name': 'checkbox', 'label': 'Multiple-choice selection', 'category': 'Selection', 'schema': {'options': [{'label': 'string', 'value': 'string'}], 'minSelections': 'number', 'maxSelections': 'number'}},
            {'name': 'dropdown', 'label': 'Dropdown selection', 'category': 'Selection', 'schema': {'options': [{'label': 'string', 'value': 'string'}]}},
            {'name': 'select', 'label': 'Dropdown selection', 'category': 'Selection', 'schema': {'options': [{'label': 'string', 'value': 'string'}]}},

            # Media
            {'name': 'image', 'label': 'Image/photo capture', 'category': 'Media', 'schema': {'maxPhotos': 'number', 'maxSizeMB': 'number'}},
            {'name': 'video', 'label': 'Video capture', 'category': 'Media', 'schema': {'maxSizeMB': 'number', 'maxLengthSeconds': 'number'}},
            {'name': 'voice', 'label': 'Voice recording', 'category': 'Media', 'schema': {'maxSizeMB': 'number', 'maxLengthSeconds': 'number'}},
            {'name': 'audio', 'label': 'Audio recording', 'category': 'Media', 'schema': {'maxSizeMB': 'number', 'maxLengthSeconds': 'number'}},
            {'name': 'signature', 'label': 'Signature capture', 'category': 'Media', 'schema': {}},
            {'name': 'file', 'label': 'Generic file upload', 'category': 'Media', 'schema': {'maxSizeMB': 'number', 'allowedExtensions': ['string']}},

            # GIS
            {'name': 'location', 'label': 'GPS location capture', 'category': 'Location & GIS', 'schema': {'requiredAccuracyMeters': 'number'}},
            {'name': 'point', 'label': 'GPS point capture', 'category': 'Location & GIS', 'schema': {'requiredAccuracyMeters': 'number'}},
            {'name': 'line', 'label': 'GIS line capture', 'category': 'Location & GIS', 'schema': {}},
            {'name': 'polygon', 'label': 'GIS polygon capture', 'category': 'Location & GIS', 'schema': {}},

            # Device data
            {'name': 'contact', 'label': 'Contact information', 'category': 'Device Data', 'schema': {'fields': ['string']}},

            # Advanced
            {'name': 'collection', 'label': 'Repeating subform', 'category': 'Advanced', 'schema': {
                'itemLabel': 'string',
                'minRepeats': 'number',
                'maxRepeats': 'number',
                'questions': 'array',
            }},
            {'name': 'calculated', 'label': 'Calculated field', 'category': 'Advanced', 'schema': {'expression': 'string', 'dependsOn': ['string']}},
            {'name': 'rating', 'label': 'Rating scale', 'category': 'Advanced', 'schema': {'min': 'number', 'max': 'number', 'step': 'number'}},
            {'name': 'slider', 'label': 'Slider input', 'category': 'Advanced', 'schema': {'min': 'number', 'max': 'number', 'step': 'number'}},

            # Layout (web builder / structure preview)
            {'name': 'section', 'label': 'Section header', 'category': 'Layout', 'schema': {}},
            {'name': 'group', 'label': 'Question group', 'category': 'Layout', 'schema': {}},
            {'name': 'note', 'label': 'Read-only note', 'category': 'Layout', 'schema': {}},

            # Legacy / aliases
            {'name': 'email', 'label': 'Email input', 'category': 'Basic', 'schema': {}},
            {'name': 'phone', 'label': 'Phone number input', 'category': 'Basic', 'schema': {}},
            {'name': 'url', 'label': 'URL input', 'category': 'Basic', 'schema': {}},

            # Scanning
            {'name': 'barcode', 'label': 'Barcode scanner', 'category': 'Scanning', 'schema': {}},
            {'name': 'qr', 'label': 'QR scanner', 'category': 'Scanning', 'schema': {}},
        ]

        created_count = 0
        for item in types:
            obj, created = FormFieldType.objects.get_or_create(
                name=item['name'],
                defaults={
                    'label': item['label'],
                    'category': item['category'],
                    'properties_schema': item.get('schema', {})
                }
            )
            if created:
                created_count += 1
            else:
                obj.label = item['label']
                obj.category = item['category']
                obj.properties_schema = item.get('schema', {})
                obj.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(types)} field types (Created: {created_count}).'))
