#!/usr/bin/env python3
"""
Seed ZINGSA Collect with JSON forms from a local directory via the Docker REST API.

Requires: pip install requests

Usage:
    python seed_forms.py
    python seed_forms.py --forms-dir "E:\\Downloads\\FORMS (1)\\FORMS"
    python seed_forms.py --base-url http://127.0.0.1:8206
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:8206"
DEFAULT_FORMS_DIR = Path(r"E:\Downloads\FORMS (1)\FORMS")

REGISTER_PAYLOAD = {
    "username": "zingsa_admin",
    "email": "admin@zingsa.test",
    "password": "SecureSeedPass2026!",
    "re_password": "SecureSeedPass2026!",
}

LOGIN_PAYLOAD = {
    "username": REGISTER_PAYLOAD["username"],
    "password": REGISTER_PAYLOAD["password"],
}

ORG_PAYLOAD = {"name": "ZINGSA Seed Org"}

PROJECT_PAYLOAD = {
    "name": "Master Forms Project",
    "status": "active",
}


def log_api_error(label: str, response: requests.Response) -> None:
    print(f"\n[ERROR] {label} — HTTP {response.status_code}", file=sys.stderr)
    try:
        print(json.dumps(response.json(), indent=2), file=sys.stderr)
    except ValueError:
        print(response.text, file=sys.stderr)


def request_or_fail(
    method: str,
    url: str,
    *,
    label: str,
    headers: dict | None = None,
    json_body: dict | None = None,
    allow_status: set[int] | None = None,
) -> requests.Response | None:
    allow_status = allow_status or set()
    response = requests.request(method, url, headers=headers, json=json_body, timeout=120)
    if response.status_code >= 400 and response.status_code not in allow_status:
        log_api_error(label, response)
        return None
    return response


def register_user(base_url: str) -> bool:
    url = f"{base_url}/api/auth/users/"
    response = requests.post(url, json=REGISTER_PAYLOAD, timeout=60)
    if response.status_code == 201:
        print(f"Registered user '{REGISTER_PAYLOAD['username']}'.")
        return True
    if response.status_code == 400:
        print(f"User '{REGISTER_PAYLOAD['username']}' already exists — continuing.")
        return True
    log_api_error("User registration", response)
    return False


def login(base_url: str) -> str | None:
    url = f"{base_url}/api/auth/jwt/create/"
    response = requests.post(url, json=LOGIN_PAYLOAD, timeout=60)
    if response.status_code >= 400:
        log_api_error("JWT login", response)
        return None
    token = response.json().get("access")
    if not token:
        print("[ERROR] Login succeeded but no access token in response.", file=sys.stderr)
        return None
    print("Authenticated — JWT obtained.")
    return token


def create_organization(base_url: str, headers: dict) -> str | None:
    url = f"{base_url}/api/organizations/"
    response = request_or_fail("POST", url, label="Create organization", headers=headers, json_body=ORG_PAYLOAD)
    if not response:
        return None
    org_id = response.json().get("id")
    print(f"Organization created: {org_id} (code={response.json().get('code')})")
    return org_id


def create_project(base_url: str, headers: dict, org_id: str) -> tuple[str, str] | None:
    url = f"{base_url}/api/projects/"
    payload = {**PROJECT_PAYLOAD, "organization": org_id}
    response = request_or_fail("POST", url, label="Create project", headers=headers, json_body=payload)
    if not response:
        return None
    data = response.json()
    project_id = data.get("id")
    project_code = data.get("code")
    print(f"Project created: {project_id} (code={project_code})")
    return project_id, project_code


def prepare_form_payload(raw: dict, project_code: str) -> dict:
    payload = dict(raw)
    if "projectId" not in payload:
        payload["projectId"] = project_code
    if not payload.get("geometryType"):
        payload["geometryType"] = "mixed"
    return payload


def create_and_publish_form(
    base_url: str,
    headers: dict,
    project_id: str,
    project_code: str,
    file_path: Path,
) -> bool:
    try:
        with file_path.open(encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[SKIP] {file_path.name}: cannot read JSON — {exc}", file=sys.stderr)
        return False

    if not isinstance(raw, dict):
        print(f"[SKIP] {file_path.name}: root JSON must be an object.", file=sys.stderr)
        return False

    payload = prepare_form_payload(raw, project_code)

    create_url = f"{base_url}/api/projects/{project_id}/forms/"
    create_resp = request_or_fail(
        "POST",
        create_url,
        label=f"Create form ({file_path.name})",
        headers=headers,
        json_body=payload,
    )
    if not create_resp:
        return False

    form_data = create_resp.json()
    form_id = form_data.get("id")
    title = form_data.get("title", file_path.stem)
    print(f"  Created form: {title} (id={form_id})")

    publish_url = f"{base_url}/api/forms/{form_id}/publish/"
    publish_resp = request_or_fail(
        "POST",
        publish_url,
        label=f"Publish form ({file_path.name})",
        headers=headers,
        json_body={},
    )
    if not publish_resp:
        return False

    table = publish_resp.json().get("physical_table_name", "?")
    print(f"  Published -> table: {table}")
    return True


def iter_json_files(forms_dir: Path) -> list[Path]:
    if not forms_dir.is_dir():
        return []
    return sorted(forms_dir.rglob("*.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed ZINGSA Collect forms via REST API.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument("--forms-dir", type=Path, default=DEFAULT_FORMS_DIR, help="Directory of JSON forms")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    forms_dir = args.forms_dir

    print(f"API: {base_url}")
    print(f"Forms directory: {forms_dir}")

    if not register_user(base_url):
        return 1

    token = login(base_url)
    if not token:
        return 1

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    org_id = create_organization(base_url, headers)
    if not org_id:
        return 1

    project_result = create_project(base_url, headers, org_id)
    if not project_result:
        return 1
    project_id, project_code = project_result

    json_files = iter_json_files(forms_dir)
    if not json_files:
        print(f"No .json files found under {forms_dir}", file=sys.stderr)
        return 1

    print(f"\nUploading {len(json_files)} form file(s)…\n")
    ok = 0
    failed = 0

    for path in json_files:
        print(f"-> {path.relative_to(forms_dir)}")
        if create_and_publish_form(base_url, headers, project_id, project_code, path):
            ok += 1
        else:
            failed += 1
            print(f"  Skipped due to errors.", file=sys.stderr)

    print(f"\nDone. Success: {ok}, Failed/skipped: {failed}, Total: {len(json_files)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
