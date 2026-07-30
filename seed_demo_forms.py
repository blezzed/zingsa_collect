#!/usr/bin/env python3
import os
import sys
import json
import django
from pathlib import Path

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.projects.models import Project
from apps.organizations.models import Organization
from apps.forms.services.form_services import create_form_service, publish_form_service
from django.db import transaction

User = get_user_model()

def seed_demo_forms(testform_dir):
    try:
        user, _ = User.objects.get_or_create(username='demo_user', defaults={'email': 'demo@zingsa.com'})
        user.set_password('demo_password')
        user.save()
        
        org, _ = Organization.objects.get_or_create(code='ORG-DEMO-001', defaults={'name': 'Demo Organization'})
        project, _ = Project.objects.get_or_create(
            code='PROJ-DEMO-001', 
            defaults={
                'name': 'Demo Project',
                'owner': user,
                'organization': org,
                'status': 'active'
            }
        )

        forms_dir = Path(testform_dir)
        if not forms_dir.exists():
            print(f"Directory {forms_dir} does not exist.")
            return

        json_files = list(forms_dir.rglob("*.json"))
        if not json_files:
            print(f"No JSON files found in {forms_dir}")
            return

        print(f"Found {len(json_files)} form files.")

        for filepath in json_files:
            with open(filepath, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # create form
            title = schema.get('title', filepath.stem)
            try:
                with transaction.atomic():
                    form = create_form_service(
                        project=project,
                        title=title,
                        created_by=user,
                        schema=schema,
                        mode=schema.get('mode', 'form_first'),
                        geometry_type=schema.get('geometryType', 'none'),
                        description=schema.get('description')
                    )
                    form.is_demo = True
                    form.save()
                    publish_form_service(form, created_by=user)
                    print(f"Seeded demo form: {title}")
            except Exception as e:
                print(f"Error seeding {title}: {e}")

    except Exception as e:
        print(f"Global error: {e}")

if __name__ == '__main__':
    testform_dir = sys.argv[1] if len(sys.argv) > 1 else '/tmp/TESTFORM'
    seed_demo_forms(testform_dir)
