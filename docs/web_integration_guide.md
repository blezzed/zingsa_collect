# ZINGSA Collect: Web API Integration Guide

This document outlines the complete sequence of API calls the web frontend should make to authenticate, navigate the project hierarchy, and visualize the submitted data on the map and attribute tables.

All examples assume the backend is running at `http://172.30.5.24:8206`.

---

## 1. Authentication
The web app must log in to obtain a JWT token.

**Request:** `POST /api/auth/jwt/create/`
```json
{
  "username": "zingsa_admin",
  "password": "SecureSeedPass2026!"
}
```

**Response:**
```json
{
  "access": "eyJhbGciOi...",
  "refresh": "eyJhbGciOi...",
  "user": {
    "id": 1,
    "username": "admin"
  }
}
```
> [!IMPORTANT]
> Attach the `access` token as an `Authorization: Bearer <access_token>` header on all subsequent requests.

---

## 2. Fetch Projects
Retrieve all projects the logged-in user has access to across all organizations.

**Request:** `GET /api/projects/`

**Response:**
```json
[
  {
    "id": "f875cc71-3722-42a9-83de-ea75c242d621",
    "name": "Harare Road Maintenance",
    "code": "PROJ-HRE-01",
    "status": "active"
  }
]
```

---

## 3. Fetch Forms for a Selected Project
When the user clicks a project, fetch the forms associated with it. 
Look at the `has_geodata` flag to determine if you need to render a map view or just an attribute table!

**Request:** `GET /api/projects/f875cc71-3722-42a9-83de-ea75c242d621/forms/`

**Response:**
```json
[
  {
    "id": "65fa6507-819f-4f4e-9f37-5823dcee6c5e",
    "title": "Pothole Survey",
    "slug": "pothole-survey",
    "has_geodata": true,
    "status": "published",
    "current_version": "743201aa-5e9e-4499-b338-3ccf9e95f631"
  }
]
```

---

## 4. Map Visualization (GeoJSON)
If `has_geodata` is true, call this highly optimized endpoint to fetch *only* the map coordinates. This ensures the map renders instantly even with 100,000+ points because it strips out heavy text/media data.

**Request:** `GET /api/web/forms/65fa6507-819f-4f4e-9f37-5823dcee6c5e/geojson/`

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [31.05, -17.82]
      },
      "properties": {
        "id": 1
      }
    }
  ]
}
```

---

## 5. Attribute Table: Headers
To render the grid/table view, first fetch the dynamic columns for the form.

**Request:** `GET /api/web/forms/65fa6507-819f-4f4e-9f37-5823dcee6c5e/columns/`

**Response:**
```json
[
  { "id": "id", "label": "ID", "type": "number" },
  { "id": "synced_at", "label": "Synced At", "type": "datetime" },
  { "id": "road_name", "label": "Road Name", "type": "text" },
  { "id": "severity", "label": "Pothole Severity", "type": "select_one" },
  { "id": "photo", "label": "Photo", "type": "image" }
]
```

---

## 6. Attribute Table: Paginated Data
Fetch the actual rows for the table. This endpoint automatically detects and **removes** heavy geometry columns from the payload, so your table loads blazingly fast.

**Request:** `GET /api/web/forms/65fa6507-819f-4f4e-9f37-5823dcee6c5e/data/?page=1&limit=50`

**Response:**
```json
{
  "total": 142,
  "page": 1,
  "limit": 50,
  "data": [
    {
      "id": 1,
      "synced_at": "2026-05-28T09:30:00Z",
      "road_name": "Samora Machel Ave",
      "severity": "High",
      "photo": "http://172.30.5.24:8206/media/uploads/2026/05/pothole1.jpg"
    }
  ]
}
```

---

## 7. Row Detail View
When a user clicks a row on the Attribute Table or a pin on the Map (using the `id` property from the GeoJSON), fetch the 100% full detail for that specific record (which includes everything: text, geometries, and media).

**Request:** `GET /api/web/forms/65fa6507-819f-4f4e-9f37-5823dcee6c5e/data/1/`

**Response:**
```json
{
  "metadata": {
    "id": "e7b1c...",
    "device_id": "samsung-tablet-1",
    "submitted_by": "john_doe",
    "synced_at": "2026-05-28T09:30:00Z"
  },
  "answers": {
    "id": 1,
    "road_name": "Samora Machel Ave",
    "severity": "High",
    "photo": "http://127.0.0.1:8206/media/uploads/2026/05/pothole1.jpg",
    "geom_point": {
        "type": "Point",
        "coordinates": [31.05, -17.82]
    }
  }
}
```
