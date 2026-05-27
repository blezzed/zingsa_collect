from django.core.management.base import BaseCommand
from apps.forms.models import FormFieldType

class Command(BaseCommand):
    help = 'Seeds the database with default Form Field Types from the ZINGSA Collect documentation'

    def handle(self, *args, **kwargs):
        types = [
            # Basic
            {'name': 'text', 'label': 'Single-line text input', 'category': 'Basic'},
            {'name': 'textarea', 'label': 'Multi-line text input', 'category': 'Basic'},
            {'name': 'email', 'label': 'Email input', 'category': 'Basic'},
            {'name': 'phone', 'label': 'Phone number input', 'category': 'Basic'},
            {'name': 'url', 'label': 'URL input', 'category': 'Basic'},
            {'name': 'number', 'label': 'Numeric input', 'category': 'Basic'},
            
            # Date/Time
            {'name': 'date', 'label': 'Date picker', 'category': 'Date & Time'},
            {'name': 'time', 'label': 'Time picker', 'category': 'Date & Time'},
            
            # Selection
            {'name': 'radio', 'label': 'Single-choice selection', 'category': 'Selection'},
            {'name': 'checkbox', 'label': 'Multiple-choice selection', 'category': 'Selection'},
            {'name': 'dropdown', 'label': 'Dropdown selection', 'category': 'Selection'},
            
            # Media
            {'name': 'image', 'label': 'Image/photo capture', 'category': 'Media'},
            {'name': 'video', 'label': 'Video capture', 'category': 'Media'},
            {'name': 'voice', 'label': 'Voice recording', 'category': 'Media'},
            {'name': 'audio', 'label': 'Audio recording', 'category': 'Media'},
            {'name': 'signature', 'label': 'Signature capture', 'category': 'Media'},
            {'name': 'file', 'label': 'Generic file upload', 'category': 'Media'},
            
            # GIS
            {'name': 'location', 'label': 'GPS location capture', 'category': 'GIS'},
            {'name': 'point', 'label': 'GPS point capture', 'category': 'GIS'},
            {'name': 'line', 'label': 'GIS line capture', 'category': 'GIS'},
            {'name': 'polygon', 'label': 'GIS polygon capture', 'category': 'GIS'},
            
            # Scanning
            {'name': 'barcode', 'label': 'Barcode scanner', 'category': 'Scanning'},
            {'name': 'qr', 'label': 'QR scanner', 'category': 'Scanning'},
        ]

        created_count = 0
        for item in types:
            obj, created = FormFieldType.objects.get_or_create(
                name=item['name'],
                defaults={
                    'label': item['label'],
                    'category': item['category']
                }
            )
            if created:
                created_count += 1
            else:
                # Update existing if label/category changed
                obj.label = item['label']
                obj.category = item['category']
                obj.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(types)} field types (Created: {created_count}).'))
