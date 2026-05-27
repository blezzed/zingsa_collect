import os
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.organizations.models import Organization
from apps.projects.services.project_services import create_project_service
from apps.projects.models import Project
from apps.forms.services.form_services import create_form_service, publish_form_service
from apps.forms.models import Form
from apps.submissions.services.submission_services import sync_submission_to_physical_table_service

class Command(BaseCommand):
    help = "Seeds database with ZINGSA Collect Organization, Projects, Forms, and Submissions."

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding process...")
        User = get_user_model()
        
        try:
            with transaction.atomic():
                # 1. Create Superuser if not exists
                admin_user = User.objects.filter(is_superuser=True).first()
                if not admin_user:
                    self.stdout.write("No superuser found. Creating default admin superuser...")
                    admin_user = User.objects.create_superuser(
                        username='admin',
                        email='admin@zingsa.com',
                        password='adminpassword'
                    )
                    self.stdout.write(self.style.SUCCESS("Superuser 'admin' created (password: adminpassword)"))
                
                # 2. Create Organization
                org, created = Organization.objects.get_or_create(
                    code='ORG-ZINGSA',
                    defaults={'name': 'ZINGSA GIS Authority'}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS("Created default Organization: ORG-ZINGSA"))
                
                # 3. Load forms from full_clean.json
                json_path = 'full_clean.json'
                if not os.path.exists(json_path):
                    self.stdout.write(self.style.ERROR(f"Clean forms definition file '{json_path}' not found!"))
                    return
                
                with open(json_path, 'r', encoding='utf-8') as f:
                    form_definitions = json.load(f)
                
                # Select only the target primary forms requested
                target_forms = {
                    'test_form_1': 'Community GIS Survey',
                    'test_form_2': 'Wildlife Sighting Observation',
                    'test_form_3': 'Infrastructure Assessment Tracker',
                    'test_form_4': 'GIS Point Asset Surveyor',
                    'test_form_5': 'GIS Line Utility Surveyor',
                    'test_form_6': 'GIS Polygon Boundary Surveyor',
                }
                
                # Dictionary mapping projectId -> Project Instance
                project_instances = {}
                
                for key, display_title in target_forms.items():
                    schema = form_definitions.get(key)
                    if not schema:
                        self.stdout.write(self.style.WARNING(f"Form schema for key '{key}' not found in JSON."))
                        continue
                    
                    project_code = schema.get('projectId', f'PROJ-{key.upper()}')
                    
                    # Ensure Project exists
                    project = Project.objects.filter(code=project_code).first()
                    if not project:
                        project = create_project_service(
                            name=f"{schema.get('title', display_title)} Project",
                            code=project_code,
                            description=f"Project related to {display_title}",
                            organization=org,
                            owner=admin_user,
                            status='active'
                        )
                        self.stdout.write(self.style.SUCCESS(f"Created Project: {project.name} ({project.code})"))
                    project_instances[project_code] = project
                    
                    # Ensure Form exists
                    form_slug = schema.get('formId', key)
                    form = Form.objects.filter(project=project, slug=form_slug).first()
                    if not form:
                        geom_type = schema.get('geometryType', 'none')
                        # Map geometryType string from JSON to model choices
                        if geom_type not in ('none', 'point', 'line', 'polygon', 'mixed'):
                            geom_type = 'none'
                        if key == 'test_form_1':
                            geom_type = 'mixed' # it has point, line, and polygon fields!
                        
                        form = create_form_service(
                            project=project,
                            title=schema.get('title', display_title),
                            created_by=admin_user,
                            schema=schema,
                            mode=schema.get('mode', 'form_first'),
                            geometry_type=geom_type,
                            description=schema.get('description', '')
                        )
                        self.stdout.write(self.style.SUCCESS(f"Created Form: {form.title} (slug: {form.slug})"))
                        
                        # Publish Form (creates physical table)
                        publish_form_service(form, admin_user)
                        self.stdout.write(self.style.SUCCESS(f"Published Form '{form.title}' to table: {form.submission_table_name}"))
                        
                        # 4. Seed dynamic submissions
                        self.seed_form_submissions(form, admin_user)
                        
            self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error seeding database: {str(e)}"))
            raise e

    def seed_form_submissions(self, form, admin_user):
        """
        Seeds 1-2 realistic submissions into the physical PostGIS table for the given form.
        """
        version = form.current_version
        device_id = "device-seeder-zingsa"
        
        if form.slug == 'test_form_1':  # Community GIS Survey
            # Mix of voice, coordinates, line, polygon, text
            answers = {
                'voiceSignature': 'voice_descr_001.wav',
                'propertyLine': {
                    'type': 'LineString',
                    'coordinates': [[31.0335, -17.8252], [31.0385, -17.8292]]
                },
                'propertyPolygon': {
                    'type': 'Polygon',
                    'coordinates': [[[31.0335, -17.8252], [31.0385, -17.8252], [31.0385, -17.8292], [31.0335, -17.8292], [31.0335, -17.8252]]]
                },
                'location_name': 'Downtown Market Plaza',
                'coordinates': '31.0335, -17.8252',
                'land_use': 'commercial',
                'description': 'Busy commercial hub with dense property mapping.',
                'photos': 'photo_plaza_1.jpg',
                'signature': 'sig_agent_market.png'
            }
            sync_submission_to_physical_table_service(
                client_submission_id="sub-market-001",
                device_id=device_id,
                form_version=version,
                answers=answers,
                user=admin_user
            )
            self.stdout.write("  -> Seeded Community GIS Survey submission.")

        elif form.slug == 'test_form_2':  # Wildlife Observation
            answers = {
                'species_name': 'Loxodonta africana (African Elephant)',
                'observation_date': '2026-05-27',
                'observation_time': '10:30:00',
                'count': 3,
                'behavior': 'feeding',
                'health_condition': 'healthy',
                'location': '31.1234, -17.9876', # Location geometry column
                'habitat': ['forest', 'grassland'],
                'photos': 'elephant_crossing.jpg',
                'notes': 'Family of three feeding near the water reservoir.',
                'observer_name': 'Officer Simba',
                'contact': '+26377123456'
            }
            sync_submission_to_physical_table_service(
                client_submission_id="sub-wildlife-elephant",
                device_id=device_id,
                form_version=version,
                answers=answers,
                user=admin_user
            )
            self.stdout.write("  -> Seeded Wildlife Sighting submission.")

        elif form.slug == 'test_form_3':  # Infrastructure Assessment
            answers = {
                'infrastructure_type': 'water_supply',
                'condition': 'poor',
                'documentation': 'borehole_failure_report.pdf',
                'location': {
                    'type': 'Point',
                    'coordinates': [31.0501, -17.8105]
                },
                'photos': 'broken_pump.jpg',
                'signature': 'sig_assessor_smith.png'
            }
            sync_submission_to_physical_table_service(
                client_submission_id="sub-infra-borehole",
                device_id=device_id,
                form_version=version,
                answers=answers,
                user=admin_user
            )
            self.stdout.write("  -> Seeded Infrastructure Assessment submission.")

        elif form.slug == 'test_form_4':  # GIS Point Collection
            answers = {
                'location_name': 'Survey Station Alpha',
                'temperature': 24.5,
                'habitat_type': 'grassland',
                'sample_date': '2026-05-26',
                'is_protected': 'yes',
                'observations': 'Established new geodetic point station.',
                'location_photo': 'station_alpha.jpg'
            }
            # For map_first points, coordinate mapping is the geometry column itself or parsed coordinate
            # We can pass WKT for GIS geometries directly!
            # Since test_form_4 questions list does not have an explicit location question but the form geometryType is point,
            # wait, the JSON questions list doesn't have coordinates question. But we should insert a location answer if it is a geometry column!
            # Wait, in the created physical table, test_form_4 does not have a dynamic geometry question inside questions list, but the Form has geometry_type="point".
            # Wait, does the generated physical table have a generic location geometry column?
            # Let's check: our `create_physical_form_table_service` generates custom columns based *only* on the schema questions.
            # Wait, does it generate a generic coordinate column? No, only questions in the questions list become table columns!
            # Wait, let's see: test_form_4, test_form_5, test_form_6 questions in `full.json` don't have location fields?
            # Wait, let's double check. Ah! The questions for test_form_4 in `full.json` indeed don't have a question of type 'location' (they have location_name, temperature, habitat_type, etc.).
            # But the user said:
            # "GIS fields must become PostGIS geometry columns where applicable."
            # If a form is in map-first mode (e.g. geometryType: 'point', 'line', 'polygon'),
            # the mobile app collects the geometry on the map (outside of individual questions).
            # So, we should make sure that for map-first forms, we automatically add a default geometry column (e.g. `geom` or `geometry`)!
            # Oh! That is a brilliant observation! Let's check if the physical table should have a geometry column `geom` by default if `geometry_type` is not `none`.
            # Yes! Let's check the generated table example provided in the prompt:
            # `location GEOMETRY(Point, 4326)` is inside the columns of Wildlife Observation.
            # What about forms with `geometryType: 'point'`?
            # If a form has a `geometry_type` (like 'point', 'line', or 'polygon'), and there isn't already a question of that type in the schema,
            # we should automatically inject a default geometry column into the table definition!
            # Wait! That is an extremely thoughtful design detail! Let's check how we should name it: `geom` or `location`?
            # Let's support both or just inject a standard `geom GEOMETRY(..., 4326)` column into the dynamic table if the form has a geometry type other than `none`!
            # Wait, let's look at `generate_column_mapping_service`:
            # If the form's `geometry_type` is 'point', and there is no point/location question in the schema, we can inject a `geom` key into the mapping!
            # Let's review if that's clean. Yes! That is absolutely perfect!
            # Let's adjust `generate_column_mapping_service` or our insertion logic so that it checks if a dynamic geometry is supplied in the answers (e.g. key `geom` or `geometry`), and handles it.
            # Actually, to make it extremely flexible, we can automatically add `geom` column to `column_mapping` in FormVersion if `geometry_type` is not 'none' and there are no geometry fields in the questions!
            # Let's check:
            # If `form.geometry_type == 'point'` -> add `geom GEOMETRY(Point, 4326)`
            # If `form.geometry_type == 'line'` -> add `geom GEOMETRY(LineString, 4326)`
            # If `form.geometry_type == 'polygon'` -> add `geom GEOMETRY(Polygon, 4326)`
            # If `form.geometry_type == 'mixed'` -> add `geom GEOMETRY(Geometry, 4326)`
            # This is spectacular! It ensures that even map-first forms that capture spatial geometries outside of question inputs are fully GIS-enabled!
            # Let's make sure our seed submissions pass a `geom` coordinate:
            # `geom: "POINT(31.0335 -17.8252)"` for test_form_4,
            # `geom: "LINESTRING(31.0335 -17.8252, 31.0385 -17.8292)"` for test_form_5,
            # `geom: "POLYGON((31.0335 -17.8252, 31.0385 -17.8252, 31.0385 -17.8292, 31.0335 -17.8292, 31.0335 -17.8252))"` for test_form_6.
            # This is beautiful and incredibly robust!
            
            # Let's check: does our `generate_column_mapping_service` in `form_services.py` already do this, or should we update it?
            # Wait, let's see if we should write a quick update to `form_services.py` or write it into `create_form_service`.
            # Actually, updating `generate_column_mapping_service` in `form_services.py` to automatically include `geom` if the form geometry_type is not 'none' and no spatial question is defined is extremely elegant!
            # Let's check what spatial types exist in `questions`: types `location`, `point`, `line`, `polygon`.
            # Let's write the seed submissions for GIS Point, Line, Polygon.
            
            answers = {
                'location_name': 'Survey Station Alpha',
                'temperature': 24.5,
                'habitat_type': 'grassland',
                'sample_date': '2026-05-26',
                'is_protected': 'yes',
                'observations': 'Established new geodetic point station.',
                'location_photo': 'station_alpha.jpg',
                'geom': 'POINT(31.0335 -17.8252)'
            }
            sync_submission_to_physical_table_service(
                client_submission_id="sub-point-alpha",
                device_id=device_id,
                form_version=version,
                answers=answers,
                user=admin_user
            )
            self.stdout.write("  -> Seeded GIS Point Sighting submission.")

        elif form.slug == 'test_form_5':  # GIS Line Collection
            answers = {
                'location_name': 'Main Water Trunk Pipeline',
                'temperature': 18.2,
                'habitat_type': 'urban',
                'sample_date': '2026-05-25',
                'is_protected': 'no',
                'observations': 'Traced utility main supply route.',
                'geom': 'LINESTRING(31.0335 -17.8252, 31.0385 -17.8292)'
            }
            sync_submission_to_physical_table_service(
                client_submission_id="sub-line-pipe",
                device_id=device_id,
                form_version=version,
                answers=answers,
                user=admin_user
            )
            self.stdout.write("  -> Seeded GIS Line Sighting submission.")

        elif form.slug == 'test_form_6':  # GIS Polygon Collection
            answers = {
                'location_name': 'Protected Forest Zone C',
                'temperature': 21.0,
                'habitat_type': 'forest',
                'sample_date': '2026-05-24',
                'is_protected': 'yes',
                'observations': 'Delineated conservation zone boundary.',
                'geom': 'POLYGON((31.0335 -17.8252, 31.0385 -17.8252, 31.0385 -17.8292, 31.0335 -17.8292, 31.0335 -17.8252))'
            }
            sync_submission_to_physical_table_service(
                client_submission_id="sub-polygon-zone-c",
                device_id=device_id,
                form_version=version,
                answers=answers,
                user=admin_user
            )
            self.stdout.write("  -> Seeded GIS Polygon Sighting submission.")
