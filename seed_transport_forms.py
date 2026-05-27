#!/usr/bin/env python3
"""
Seed the National Highway & Transport Survey project with three production GIS forms.

Requires: pip install requests

Usage:
    python seed_transport_forms.py
    python seed_transport_forms.py --base-url http://127.0.0.1:8206
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:8206"

LOGIN_PAYLOAD = {
    "username": "zingsa_admin",
    "password": "SecureSeedPass2026!",
}

PROJECT_PAYLOAD = {
    "name": "National Highway & Transport Survey",
    "status": "active",
}

CREATED_BY = {
    "name": "ZINGSA Transport Division",
    "email": "transport@zingsa.org",
}


def log_api_error(label: str, response: requests.Response) -> None:
    print(f"\n[ERROR] {label} — HTTP {response.status_code}", file=sys.stderr)
    try:
        print(json.dumps(response.json(), indent=2), file=sys.stderr)
    except ValueError:
        print(response.text, file=sys.stderr)


def api_request(
    method: str,
    url: str,
    *,
    label: str,
    headers: dict | None = None,
    json_body: dict | None = None,
) -> requests.Response:
    try:
        response = requests.request(
            method, url, headers=headers, json=json_body, timeout=120
        )
    except requests.RequestException as exc:
        print(f"\n[ERROR] {label} — request failed: {exc}", file=sys.stderr)
        raise

    if response.status_code >= 400:
        log_api_error(label, response)
        raise RuntimeError(f"{label} failed with HTTP {response.status_code}")
    return response


def login(base_url: str) -> str:
    url = f"{base_url}/api/auth/jwt/create/"
    response = api_request("POST", url, label="JWT login", json_body=LOGIN_PAYLOAD)
    token = response.json().get("access")
    if not token:
        raise RuntimeError("Login succeeded but no access token returned.")
    print("Authenticated successfully.")
    return token


def get_first_organization_id(base_url: str, headers: dict) -> str:
    url = f"{base_url}/api/organizations/"
    response = api_request("GET", url, label="List organizations", headers=headers)
    orgs = response.json()
    if not orgs:
        raise RuntimeError("No organizations found for this user. Run seed_forms.py first.")
    org_id = orgs[0]["id"]
    print(f"Using organization: {orgs[0].get('name')} ({org_id})")
    return org_id


def create_project(base_url: str, headers: dict, org_id: str) -> tuple[str, str]:
    url = f"{base_url}/api/projects/"
    payload = {**PROJECT_PAYLOAD, "organization": org_id}
    response = api_request("POST", url, label="Create project", headers=headers, json_body=payload)
    data = response.json()
    project_id = data["id"]
    project_code = data["code"]
    print(f"Project created: {data['name']} (id={project_id}, code={project_code})")
    return project_id, project_code


def _base_form_meta(form_id: str, title: str, description: str, project_code: str, geometry_type: str, mode: str) -> dict:
    return {
        "id": form_id,
        "formId": form_id,
        "title": title,
        "description": description,
        "version": "1.0",
        "mode": mode,
        "projectId": project_code,
        "geometryType": geometry_type,
        "category": "transport",
        "createdBy": CREATED_BY,
        "createdDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def build_road_surface_form(project_code: str) -> dict:
    meta = _base_form_meta(
        form_id="transport_road_surface_quality_v1",
        title="Road Surface Quality & Defect Assessment",
        description=(
            "Field assessment of paved and unpaved road segments for national highway "
            "maintenance planning. Captures pavement inventory, surface condition index (SCI), "
            "defect taxonomy, photographic evidence, and maintenance prioritisation along "
            "the surveyed alignment."
        ),
        project_code=project_code,
        geometry_type="line",
        mode="map_first",
    )
    meta["questions"] = [
        {
            "id": "assessed_segment",
            "type": "line",
            "label": "Assessed Road Segment",
            "required": True,
            "hint": "Trace the centreline of the road segment being assessed, from chainage start to end.",
        },
        {
            "id": "road_segment_id",
            "type": "text",
            "label": "Road Segment ID",
            "required": True,
            "hint": "Official segment identifier from the highway asset register (e.g. A4-KM12.4-NB).",
            "placeholder": "e.g. A4-KM12.4-NB",
            "minLength": 3,
            "maxLength": 64,
        },
        {
            "id": "highway_designation",
            "type": "text",
            "label": "Highway / Route Designation",
            "required": True,
            "hint": "National route number or local road name.",
            "placeholder": "e.g. A4 Harare–Mutare Highway",
            "maxLength": 120,
        },
        {
            "id": "chainage_start_km",
            "type": "number",
            "label": "Chainage Start (km)",
            "required": True,
            "numericType": "decimal",
            "min": 0,
            "max": 9999,
            "hint": "Kilometre post at the start of the assessed segment.",
        },
        {
            "id": "chainage_end_km",
            "type": "number",
            "label": "Chainage End (km)",
            "required": True,
            "numericType": "decimal",
            "min": 0,
            "max": 9999,
            "hint": "Kilometre post at the end of the assessed segment.",
        },
        {
            "id": "segment_length_m",
            "type": "number",
            "label": "Segment Length (m)",
            "required": False,
            "numericType": "integer",
            "min": 1,
            "max": 50000,
            "hint": "Measured or GIS-derived length of the assessed segment.",
        },
        {
            "id": "pavement_type",
            "type": "dropdown",
            "label": "Pavement Type",
            "required": True,
            "hint": "Dominant structural pavement layer at the surface.",
            "options": [
                {"value": "asphalt", "label": "Asphalt"},
                {"value": "concrete", "label": "Concrete"},
                {"value": "gravel", "label": "Gravel"},
                {"value": "unpaved", "label": "Unpaved"},
            ],
        },
        {
            "id": "carriageway_lanes",
            "type": "number",
            "label": "Number of Lanes",
            "required": False,
            "numericType": "integer",
            "min": 1,
            "max": 8,
            "hint": "Total lanes in the assessed direction(s) of travel.",
        },
        {
            "id": "surface_condition_index",
            "type": "number",
            "label": "Surface Condition Index (1–10)",
            "required": True,
            "numericType": "integer",
            "min": 1,
            "max": 10,
            "hint": "1 = failed pavement, 10 = excellent. Use national SCI guidance.",
        },
        {
            "id": "primary_defect_type",
            "type": "dropdown",
            "label": "Primary Defect Type",
            "required": True,
            "hint": "Most severe or extensive defect observed along the segment.",
            "options": [
                {"value": "potholes", "label": "Potholes"},
                {"value": "cracking", "label": "Cracking"},
                {"value": "rutting", "label": "Rutting"},
                {"value": "none", "label": "None"},
            ],
        },
        {
            "id": "defect_severity",
            "type": "dropdown",
            "label": "Defect Severity",
            "required": True,
            "hint": "Severity rating for the primary defect type.",
            "options": [
                {"value": "minor", "label": "Minor — cosmetic / early stage"},
                {"value": "moderate", "label": "Moderate — functional impact emerging"},
                {"value": "severe", "label": "Severe — safety or structural concern"},
                {"value": "critical", "label": "Critical — immediate intervention required"},
            ],
        },
        {
            "id": "defect_extent_percent",
            "type": "number",
            "label": "Defect Extent (% of segment)",
            "required": False,
            "numericType": "integer",
            "min": 0,
            "max": 100,
            "hint": "Approximate percentage of segment length affected by the primary defect.",
        },
        {
            "id": "defect_photo",
            "type": "image",
            "label": "Defect Photograph",
            "required": True,
            "maxPhotos": 3,
            "hint": "Capture clear photos of the worst defect location; include scale reference where possible.",
        },
        {
            "id": "drainage_condition",
            "type": "dropdown",
            "label": "Side Drain / Shoulder Drainage",
            "required": False,
            "options": [
                {"value": "adequate", "label": "Adequate"},
                {"value": "partially_blocked", "label": "Partially Blocked"},
                {"value": "blocked", "label": "Blocked"},
                {"value": "not_present", "label": "Not Present"},
            ],
        },
        {
            "id": "maintenance_urgency",
            "type": "dropdown",
            "label": "Maintenance Urgency",
            "required": True,
            "hint": "Recommended response timeframe for maintenance programming.",
            "options": [
                {"value": "low", "label": "Low — routine cycle"},
                {"value": "medium", "label": "Medium — schedule within 12 months"},
                {"value": "high", "label": "High — schedule within 90 days"},
                {"value": "critical", "label": "Critical — emergency works"},
            ],
        },
        {
            "id": "inspector_remarks",
            "type": "textarea",
            "label": "Inspector Remarks",
            "required": False,
            "minLength": 0,
            "maxLength": 2000,
            "placeholder": "Additional observations, detour recommendations, or coordination notes.",
        },
    ]
    return meta


def build_traffic_flow_form(project_code: str) -> dict:
    meta = _base_form_meta(
        form_id="transport_intersection_traffic_v1",
        title="Intersection Traffic & Pedestrian Audit",
        description=(
            "Structured intersection audit for national transport corridor studies. "
            "Records peak-period vehicle and pedestrian volumes, heavy vehicle mix, "
            "crossing facilities, signal operations, and qualitative inspector notes "
            "at signalised and unsignalised junctions."
        ),
        project_code=project_code,
        geometry_type="point",
        mode="map_first",
    )
    meta["questions"] = [
        {
            "id": "intersection_location",
            "type": "location",
            "label": "Intersection GPS Location",
            "required": True,
            "hint": "Stand at the approximate centre of the junction and capture the point.",
        },
        {
            "id": "intersection_name",
            "type": "text",
            "label": "Intersection Name",
            "required": True,
            "hint": "Official or commonly used junction name.",
            "placeholder": "e.g. Samora Machel & Leopold Takawira",
            "minLength": 3,
            "maxLength": 150,
        },
        {
            "id": "junction_type",
            "type": "dropdown",
            "label": "Junction Type",
            "required": True,
            "options": [
                {"value": "signalised", "label": "Signalised"},
                {"value": "roundabout", "label": "Roundabout"},
                {"value": "priority", "label": "Priority (give-way)"},
                {"value": "uncontrolled", "label": "Uncontrolled"},
            ],
        },
        {
            "id": "audit_date",
            "type": "date",
            "label": "Audit Date",
            "required": True,
        },
        {
            "id": "audit_time_period",
            "type": "dropdown",
            "label": "Audit Time Period",
            "required": True,
            "hint": "Peak period during which counts were conducted.",
            "options": [
                {"value": "morning_peak", "label": "Morning Peak"},
                {"value": "midday", "label": "Midday"},
                {"value": "evening_peak", "label": "Evening Peak"},
                {"value": "night", "label": "Night"},
            ],
        },
        {
            "id": "count_duration_minutes",
            "type": "number",
            "label": "Count Duration (minutes)",
            "required": True,
            "numericType": "integer",
            "min": 15,
            "max": 180,
            "hint": "Standard count window (typically 60 or 120 minutes).",
        },
        {
            "id": "vehicle_volume_per_hour",
            "type": "number",
            "label": "Vehicle Volume (vehicles/hour)",
            "required": True,
            "numericType": "integer",
            "min": 0,
            "max": 50000,
            "hint": "Total all-direction vehicle flow extrapolated to hourly rate.",
        },
        {
            "id": "heavy_vehicles_percentage",
            "type": "number",
            "label": "Heavy Vehicles (%)",
            "required": True,
            "numericType": "decimal",
            "min": 0,
            "max": 100,
            "hint": "Percentage of trucks, buses, and articulated vehicles in the count.",
        },
        {
            "id": "pedestrian_crossings_available",
            "type": "boolean",
            "label": "Formal Pedestrian Crossings Available",
            "required": True,
            "hint": "True if marked crossings, refuge islands, or signalised pedestrian stages exist.",
        },
        {
            "id": "pedestrian_volume_per_hour",
            "type": "number",
            "label": "Pedestrian Volume (pedestrians/hour)",
            "required": True,
            "numericType": "integer",
            "min": 0,
            "max": 20000,
        },
        {
            "id": "cyclist_volume_per_hour",
            "type": "number",
            "label": "Cyclist Volume (cycles/hour)",
            "required": False,
            "numericType": "integer",
            "min": 0,
            "max": 5000,
        },
        {
            "id": "traffic_light_functional",
            "type": "boolean",
            "label": "Traffic Signals Functional",
            "required": True,
            "hint": "False if signals are flashing, off, or vandalised. N/A if unsignalised — select True.",
        },
        {
            "id": "signal_cycle_observed",
            "type": "number",
            "label": "Observed Signal Cycle Length (seconds)",
            "required": False,
            "numericType": "integer",
            "min": 30,
            "max": 300,
        },
        {
            "id": "conflict_observations",
            "type": "checkbox",
            "label": "Observed Conflict Types",
            "required": False,
            "hint": "Select all conflict types witnessed during the count period.",
            "options": [
                {"value": "vehicle_pedestrian", "label": "Vehicle–Pedestrian"},
                {"value": "vehicle_vehicle", "label": "Vehicle–Vehicle"},
                {"value": "vehicle_cyclist", "label": "Vehicle–Cyclist"},
                {"value": "none", "label": "None Observed"},
            ],
        },
        {
            "id": "inspector_audio_notes",
            "type": "voice",
            "label": "Inspector Audio Notes",
            "required": False,
            "hint": "Record operational observations, near-misses, or signal timing issues.",
        },
        {
            "id": "audit_summary",
            "type": "textarea",
            "label": "Audit Summary",
            "required": False,
            "maxLength": 1500,
            "placeholder": "Capacity assessment, recommended improvements, and coordination requirements.",
        },
    ]
    return meta


def build_transit_stop_form(project_code: str) -> dict:
    meta = _base_form_meta(
        form_id="transport_transit_stop_audit_v1",
        title="Public Transit Stop Infrastructure Audit",
        description=(
            "Infrastructure condition survey for public transport stops along national "
            "and urban corridors. Documents shelter, accessibility, lighting, signage, "
            "and passenger amenity standards for bus, BRT, and light-rail interfaces."
        ),
        project_code=project_code,
        geometry_type="point",
        mode="form_first",
    )
    meta["questions"] = [
        {
            "id": "stop_location",
            "type": "location",
            "label": "Transit Stop Location",
            "required": True,
            "hint": "Capture the stop pole or shelter centroid.",
        },
        {
            "id": "stop_id",
            "type": "text",
            "label": "Stop ID",
            "required": True,
            "hint": "Operator or municipal asset register identifier.",
            "placeholder": "e.g. BRT-HRE-0142",
            "minLength": 2,
            "maxLength": 64,
        },
        {
            "id": "stop_name",
            "type": "text",
            "label": "Stop Name",
            "required": True,
            "maxLength": 120,
            "hint": "Passenger-facing stop name on signage.",
        },
        {
            "id": "transit_mode",
            "type": "dropdown",
            "label": "Transit Mode",
            "required": True,
            "options": [
                {"value": "bus", "label": "Bus"},
                {"value": "light_rail", "label": "Light Rail"},
                {"value": "brt", "label": "BRT"},
            ],
        },
        {
            "id": "routes_served",
            "type": "text",
            "label": "Routes Served",
            "required": False,
            "placeholder": "e.g. R1, R4, ZUPCO 42",
            "maxLength": 200,
            "hint": "Comma-separated route numbers observed on signage or timetables.",
        },
        {
            "id": "has_shelter",
            "type": "boolean",
            "label": "Passenger Shelter Present",
            "required": True,
        },
        {
            "id": "shelter_condition",
            "type": "dropdown",
            "label": "Shelter Condition",
            "required": True,
            "hint": "If no shelter, select Poor and note in comments.",
            "options": [
                {"value": "excellent", "label": "Excellent"},
                {"value": "good", "label": "Good"},
                {"value": "poor", "label": "Poor"},
                {"value": "vandalized", "label": "Vandalized"},
            ],
        },
        {
            "id": "seating_available",
            "type": "boolean",
            "label": "Seating Available",
            "required": False,
        },
        {
            "id": "wheelchair_accessible",
            "type": "boolean",
            "label": "Wheelchair Accessible",
            "required": True,
            "hint": "Level boarding, ramp, or compliant access path to boarding area.",
        },
        {
            "id": "lighting_functional",
            "type": "boolean",
            "label": "Lighting Functional",
            "required": True,
            "hint": "Assess at dusk if possible; note if not observable during day audit.",
        },
        {
            "id": "real_time_display",
            "type": "boolean",
            "label": "Real-Time Passenger Information Display",
            "required": False,
        },
        {
            "id": "safety_rating",
            "type": "number",
            "label": "Perceived Safety Rating (1–5)",
            "required": False,
            "numericType": "integer",
            "min": 1,
            "max": 5,
            "hint": "Inspector subjective safety score for waiting passengers.",
        },
        {
            "id": "stop_photo",
            "type": "image",
            "label": "Stop Photograph",
            "required": True,
            "maxPhotos": 4,
            "hint": "Wide shot showing shelter, signage, and immediate road environment.",
        },
        {
            "id": "general_comments",
            "type": "text",
            "label": "General Comments",
            "required": False,
            "maxLength": 1000,
            "placeholder": "Maintenance backlog, vandalism, accessibility gaps, or operator coordination notes.",
        },
    ]
    return meta


def create_and_publish_form(
    base_url: str,
    headers: dict,
    project_id: str,
    schema: dict,
    form_label: str,
) -> None:
    create_url = f"{base_url}/api/projects/{project_id}/forms/"
    create_resp = api_request(
        "POST",
        create_url,
        label=f"Create form ({form_label})",
        headers=headers,
        json_body=schema,
    )
    form_id = create_resp.json()["id"]
    title = create_resp.json().get("title", form_label)
    print(f"  Created: {title} (id={form_id})")

    publish_url = f"{base_url}/api/forms/{form_id}/publish/"
    publish_resp = api_request(
        "POST",
        publish_url,
        label=f"Publish form ({form_label})",
        headers=headers,
        json_body={},
    )
    table = publish_resp.json().get("physical_table_name", "?")
    print(f"  Published -> {table}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed transport GIS forms via REST API.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    print(f"ZINGSA Collect Transport Seeder")
    print(f"API: {base_url}\n")

    try:
        token = login(base_url)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        org_id = get_first_organization_id(base_url, headers)
        project_id, project_code = create_project(base_url, headers, org_id)

        forms = [
            ("Road Surface Quality", build_road_surface_form(project_code)),
            ("Traffic Flow & Pedestrian", build_traffic_flow_form(project_code)),
            ("Public Transit Stop", build_transit_stop_form(project_code)),
        ]

        print(f"\nUploading and publishing {len(forms)} transport form(s)...\n")
        for label, schema in forms:
            print(f"-> {label}")
            create_and_publish_form(base_url, headers, project_id, schema, label)

        print("\nTransport seeding completed successfully.")
        return 0

    except (RuntimeError, requests.RequestException) as exc:
        print(f"\nSeeding aborted: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
