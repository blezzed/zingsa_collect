# Date formats for the mobile app

A `date` question can record a full day, a month and year, or a year. The attribute is `dateFormat`. Forms saved before this attribute existed do not have it, and those forms stay full dates.

The database column is still `DATE`. A later form version can change `dateFormat` without a table change. Sorting stays in calendar order.

## Attribute

`dateFormat` is allowed only on `type: "date"`.

| `dateFormat` | What the collector picks | Send this string | Stored | Returned by the web data API and exports |
|---|---|---|---|---|
| omitted, or `"full_date"` | Day, month and year | `"2026-10-22"` | `2026-10-22` | `"2026-10-22"` |
| `"month_year"` | Month and year | `"2026-10"` | `2026-10-01` | `"2026-10"` |
| `"year"` | Year | `"2026"` | `2026-01-01` | `"2026"` |

Month and day are always two digits. The year is four digits. Do not send a time.

Read APIs format the value with the **published** question's `dateFormat`. Sync converts with the **form version on that submission** (the schema the device downloaded).

## Sample question

```json
{
  "id": "survey_month",
  "type": "date",
  "label": "Survey month",
  "required": true,
  "dateFormat": "month_year"
}
```

A full date, including every existing form that has no `dateFormat`:

```json
{
  "id": "event_date",
  "type": "date",
  "label": "Event date"
}
```

The same attribute works on a `date` question inside a `group` or `section`. Those answers are still top-level keys in `answers`, one per question id.

## What to send

Single sync is `POST /api/sync/submissions/`. Bulk sync is `POST /api/sync/submissions/bulk/`. Put the string on the question id:

```json
{
  "device_id": "device-1",
  "client_submission_id": "local-100",
  "form_version_id": "VERSION-UUID",
  "answers": {
    "event_date": "2026-10-22",
    "survey_month": "2026-10",
    "survey_year": "2026"
  }
}
```

Empty answers stay empty. Send `null` or omit the key. Do not send `""` for a date you want stored as empty; an empty string is rejected by the `DATE` column, as it is today.

### Dates inside a collection

A `collection` is stored as JSON, not in a `DATE` column. Send the same strings. The server keeps them as sent (`"2026-10"`, not `"2026-10-01"`). A date question that has a `dateFormat` is checked with the same rules as a date column, including the longer values in [Older apps](#older-apps). A collection date with no `dateFormat` attribute is stored as sent and is not checked.

```json
"visits": [
  { "visited": "2026-08" }
]
```

`group` and `section` questions inside a collection item are flat on that item, keyed by question id, same as other collection fields.

## What comes back

The submissions table, the row detail `answers`, GeoJSON feature properties, and CSV, XLSX, JSON and KML exports all show the formatted string from the table above.

A `month_year` answer that was stored as `2026-10-01` comes back as `"2026-10"`. A `year` answer comes back as `"2026"`. A collection date comes back exactly as it was sent.

## Older apps

New apps should send the exact strings in the table above. An older app that ignores `dateFormat` may still send a full date, or a full date with a time, on a `month_year` or `year` question. The server accepts that and stores the shortened date, so the submission is not rejected.

| `dateFormat` | Also accepted | Stored |
|---|---|---|
| `"month_year"` | `"2026-10-22"`, `"2026-10-22T10:00:00.000"`, or `"2026-10-22 10:00:00"` | `2026-10-01` |
| `"year"` | `"2026-10"`, or `"2026-10-22"` with or without a time | `2026-01-01` |

A time suffix starts with `T` or a space. It is ignored, and the date is not converted to another timezone. The month and day must still be a real calendar date. Inside a collection the same values are accepted, and the JSON keeps the string that was sent.

## Bad values

The value must match that question's format, or one of the longer shapes above. These are rejected:

- `"2026-13"` (not a real month)
- `"2026-13-01"` and `"2026-02-30"` (not a real date)
- `"2026"` on a `month_year` question
- `"2026-10"` or `"2026"` on a `full_date` question
- a non-string

The bad field is not dropped. That whole submission is not saved, including its other answers.

This is the same failure an invalid date already causes:

- **Single sync.** The request fails. The API responds with HTTP 503, `code` `"database_error"`, and the message `"A database error occurred. Please try again later."` The raw database text is not returned on this call.
- **Bulk sync.** The HTTP call still returns 200. That item is `"status": "failed"`. Its `error` is the database message, for example `invalid input syntax for type date: "2026" (survey_month)`. Later items in the batch are still synced. A bad date inside a collection uses the repeat path in the message, for example `visits[0].visited`.

## Forms with no dateFormat

If `dateFormat` is missing, treat the question as `"full_date"`. Keep sending `"2026-10-22"`. The server stores and returns that full date. Do not start sending `"2026-10"` for those questions.
