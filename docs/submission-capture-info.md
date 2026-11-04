# GPS accuracy and device details on a submission

Project owners can later judge how accurate the GPS was when a record was captured, and which device and app version produced it, so a bad batch can be traced. The server only stores and shows what the mobile app sends. It does not read the device itself.

Older apps send nothing. That still saves the submission. A missing, malformed, or oversized `capture_info` does not reject the sync: the answers are stored, and the bad part is dropped.

Access is unchanged. Whoever can sync a submission can send this block. Whoever can read a submission, including the row detail and the submissions table, can read what was stored.

`capture_info` is stored on `SubmissionIndex`, not in the per-form `collect_*` table. Publishing a new form version copies the answer row and repoints the same index record. `capture_info` and `gps_accuracy_m` stay on that record.

There is no filter or sort by accuracy in this version.

## What the app sends

`capture_info` is optional. It sits next to `answers` on:

- `POST /api/sync/submissions/`
- `POST /api/sync/submissions/bulk/` (on each item)

`gps` is keyed by the spatial question id, because a form can hold several. The server does not check those ids against the form. An older downloaded form may still use a question id the current form no longer has. For a line or polygon, the app sends `accuracy_m` as the worst reading across that shape's points. The server then sets `gps_accuracy_m` to the largest valid `accuracy_m` in `gps`, or `null` when there is none.

### Single submission

`POST /api/sync/submissions/`

```json
{
  "device_id": "device-1",
  "client_submission_id": "local-100",
  "form_version_id": "VERSION-UUID",
  "answers": {
    "location_name": "North gate"
  },
  "capture_info": {
    "gps": {
      "site_location": {
        "accuracy_m": 8.5,
        "altitude_m": 1420.2,
        "provider": "gps",
        "captured_at": "2026-11-04T10:15:00Z",
        "mock_location": false
      },
      "route_line": {
        "accuracy_m": 22.0,
        "altitude_m": 1400.0,
        "provider": "gps",
        "captured_at": "2026-11-04T10:16:00Z",
        "mock_location": false
      }
    },
    "device": {
      "platform": "android",
      "os_version": "14",
      "manufacturer": "Samsung",
      "model": "SM-A156E",
      "app_version": "1.4.0"
    }
  }
}
```

`201 Created` the first time. `gps_accuracy_m` is `22.0`, the larger of the two readings. Other submission fields are unchanged and omitted here.

```json
{
  "success": true,
  "is_duplicate": false,
  "submission": {
    "id": "SUBMISSION-UUID",
    "capture_info": {
      "gps": {
        "site_location": {
          "accuracy_m": 8.5,
          "altitude_m": 1420.2,
          "provider": "gps",
          "captured_at": "2026-11-04T10:15:00Z",
          "mock_location": false
        },
        "route_line": {
          "accuracy_m": 22.0,
          "altitude_m": 1400.0,
          "provider": "gps",
          "captured_at": "2026-11-04T10:16:00Z",
          "mock_location": false
        }
      },
      "device": {
        "platform": "android",
        "os_version": "14",
        "manufacturer": "Samsung",
        "model": "SM-A156E",
        "app_version": "1.4.0"
      }
    },
    "gps_accuracy_m": 22.0
  }
}
```

Sending the same `device_id` and `client_submission_id` again returns `200 OK` with `is_duplicate: true` and the original `capture_info`. A different `capture_info` on that retry is ignored.

Omit `capture_info` and the submission still saves. The stored value is `{}` and `gps_accuracy_m` is `null`.

### Bulk

`POST /api/sync/submissions/bulk/`

`device_id` stays on the batch, as it does today. Each item carries its own `capture_info` next to `answers`.

```json
{
  "device_id": "device-1",
  "submissions": [
    {
      "client_submission_id": "local-100",
      "form_version_id": "VERSION-UUID",
      "answers": {
        "location_name": "North gate"
      },
      "capture_info": {
        "gps": {
          "site_location": {
            "accuracy_m": 8.5,
            "altitude_m": 1420.2,
            "provider": "gps",
            "captured_at": "2026-11-04T10:15:00Z",
            "mock_location": false
          }
        },
        "device": {
          "platform": "android",
          "os_version": "14",
          "manufacturer": "Samsung",
          "model": "SM-A156E",
          "app_version": "1.4.0"
        }
      }
    }
  ]
}
```

`200 OK`. The batch summary is unchanged. Read the stored block from the row detail. One bad `capture_info` does not fail that item or the rest of the batch.

```json
{
  "success": true,
  "total_received": 1,
  "total_success": 1,
  "total_failed": 0,
  "conflict_count": 0,
  "submissions": [
    {
      "index": 0,
      "client_submission_id": "local-100",
      "status": "success",
      "submission_id": "SUBMISSION-UUID"
    }
  ]
}
```

## What is kept

Only the keys in the sample are stored. Anything else is dropped, at every level, including `device.imei`, serial numbers, advertising ids, and names. String values are trimmed. A string longer than 100 characters is dropped, not shortened. `gps` keeps at most the first 50 entries. A question id longer than 100 characters is dropped. Question ids are not checked against the form.

| Field | Rule |
|---|---|
| `accuracy_m` | Finite number from 0 to 100000 inclusive. `true`, `"8.5"`, `-1`, `NaN`, and `Infinity` are dropped. |
| `altitude_m` | Finite number, including decimals and negatives. |
| `mock_location` | A real boolean. |
| `captured_at` | An ISO 8601 string, for example `2026-11-04T10:15:00Z`. |
| `provider`, `platform`, `os_version`, `manufacturer`, `model`, `app_version` | Trimmed strings of at most 100 characters. |

A value that fails its check is dropped. The rest of that GPS entry, and the answers, stay. `capture_info` sent as a string, a list, or a number is dropped and the submission is saved.

## Web

Authenticate the same way as the submissions table.

### Row detail

`GET /api/web/forms/<form_id>/data/<row_id>/`

The existing `metadata` block gains `capture_info` and `gps_accuracy_m`.

```json
{
  "metadata": {
    "id": "SUBMISSION-UUID",
    "capture_info": {
      "gps": {
        "site_location": {
          "accuracy_m": 8.5,
          "altitude_m": 1420.2,
          "provider": "gps",
          "captured_at": "2026-11-04T10:15:00Z",
          "mock_location": false
        }
      },
      "device": {
        "platform": "android",
        "os_version": "14",
        "manufacturer": "Samsung",
        "model": "SM-A156E",
        "app_version": "1.4.0"
      }
    },
    "gps_accuracy_m": 8.5
  },
  "answers": {
    "location_name": "North gate"
  }
}
```

`GET /api/submissions/<submission_uuid>/` returns the same two fields on `metadata`.

A row with no index, or with no `capture_info`, has `capture_info: {}` when an index exists and was saved without the block, and `gps_accuracy_m: null`.

### Submissions table

`GET /api/web/forms/<form_id>/data/`

`GET /api/web/forms/<form_id>/columns/` lists the same columns. Each data row gains:

| Column | Value |
|---|---|
| `gps_accuracy_m` | Largest stored accuracy, in metres, or empty |
| `device_model` | Manufacturer and model joined with a space, or empty |
| `app_version` | App version, or empty |

```json
{
  "data": [
    {
      "id": 1,
      "location_name": "North gate",
      "gps_accuracy_m": 22.0,
      "device_model": "Samsung SM-A156E",
      "app_version": "1.4.0"
    },
    {
      "id": 2,
      "location_name": "Old app",
      "gps_accuracy_m": "",
      "device_model": "",
      "app_version": ""
    }
  ]
}
```

The second row had no `capture_info`. The three columns are still present and empty.

These three values are loaded with one query for the rows on the page, not one query per row.

### Exports

`GET /api/web/forms/<form_id>/export/?export_format=csv`

The same three columns are on CSV, XLSX, and JSON. The header text is the column label: `GPS Accuracy (m)`, `Device Model`, `App Version`. Empty cells are blank.

CSV:

```text
ID,Submission UUID,Synced At,Name,GPS Accuracy (m),Device Model,App Version
1,...,...,North gate,22.0,Samsung SM-A156E,1.4.0
2,...,...,Old app,,,
```

JSON (`export_format=json`) uses the same ids on each object in `data`. XLSX (`export_format=xlsx`) uses the same headers on the Submissions sheet.

KML (`export_format=kml`) adds the three names to each placemark's `ExtendedData`, including when the value is empty.

```xml
<Data name="gps_accuracy_m"><value>22.0</value></Data>
<Data name="device_model"><value>Samsung SM-A156E</value></Data>
<Data name="app_version"><value>1.4.0</value></Data>
```

### A form that already has one of these question ids

If the form has a question whose id is `gps_accuracy_m`, `device_model`, or `app_version`, that question's answer is what the table and exports show. The system value is left out for that column on that form, so the two are not mixed. The other capture columns are still added. The stored `metadata.capture_info` and `metadata.gps_accuracy_m` are unchanged.

Example: a text question with id `gps_accuracy_m` and label `Survey accuracy`, answered `kept-answer`, while the app also sent a GPS accuracy of `22.0`.

The table cell and the CSV column `Survey accuracy` are `kept-answer`. There is no second `gps_accuracy_m` column. `device_model` and `app_version` still appear. Row detail metadata still has `gps_accuracy_m: 22.0`.
