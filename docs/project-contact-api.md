# Project contact details

Collectors ask the same person about all of a project's forms, so the contact lives on the project. An owner or manager sets it once. Every form in the project uses it.

The web page can prefill the inputs from `contact_suggestion` (the project owner's name and email). Those values are not stored, and nothing is shown to collectors until someone saves the contact. A new project's four contact fields are blank. The server does not copy the owner's account into them.

Saving the contact does not create a form version and does not change `checksum`, `force_update`, or `status`.

Logged-out callers never receive contact details, including on a demo form.

## Fields

| API field | Stored as | Rules |
|---|---|---|
| `contact_name` | text, max 150 | Trimmed. Optional. |
| `contact_phone` | text, max 30 | Trimmed. Optional leading `+`, then digits, spaces, hyphens, or brackets `()`. 7 to 15 digits in total. |
| `contact_email` | email, max 254 | Trimmed. Normal email validation. |
| `contact_note` | text, max 300 | Trimmed. For example `WhatsApp only, weekdays 8 to 5`. |

Send `""` or `null` to clear a field. If `contact_name` or `contact_note` is set, at least one of phone or email is required. A name or note with no way to reach the person is rejected. Sending all four blank clears the contact. Phone or email may be saved on their own.

Editing uses the existing `PATCH /api/projects/<project_id>/`. The same check that already guards project settings applies: the owner, a superuser, or anyone with the `manage_members` privilege (managers have it by default). A collector does not. A partial update is checked against the values that would be saved, not against the patch body alone.

`GET /api/projects/<project_id>/` returns the four fields to anyone who can read the project. It also returns `contact_suggestion` to people who may edit the project, and `null` to everyone else.

```json
"contact_suggestion": {"name": "Thandi Ncube", "email": "thandi@example.com"}
```

`name` is the owner's full name, or their username when the full name is blank. `email` is the owner's account email. It is read-only, it is not stored on the project, and it is never sent to collectors.

## Web

Authenticate with `Authorization: Bearer <access_token>`.

### Save

`PATCH /api/projects/aa0e1b22-3333-4c4d-8e5f-60718293a4b5/`

```json
{
  "contact_name": "Ada Maker",
  "contact_phone": "+27 82 123 4567",
  "contact_email": "ada@example.com",
  "contact_note": "WhatsApp only, weekdays 8 to 5"
}
```

`200 OK`

```json
{
  "id": "aa0e1b22-3333-4c4d-8e5f-60718293a4b5",
  "name": "Household survey",
  "contact_name": "Ada Maker",
  "contact_phone": "+27 82 123 4567",
  "contact_email": "ada@example.com",
  "contact_note": "WhatsApp only, weekdays 8 to 5",
  "contact_suggestion": {
    "name": "Thandi Ncube",
    "email": "thandi@example.com"
  },
  "status": "active"
}
```

Other project fields are unchanged and are omitted above. No form version is created. Form `status`, `checksum`, and `force_update` stay as they were.

`POST /api/projects/` ignores these four fields. The created project comes back with them blank. Use the suggestion to prefill the form, then save with `PATCH`.

### Read one project

`GET /api/projects/aa0e1b22-3333-4c4d-8e5f-60718293a4b5/`

The same four fields are on the project. `contact_suggestion` is present for an owner or manager and `null` for a collector:

```json
{
  "id": "aa0e1b22-3333-4c4d-8e5f-60718293a4b5",
  "contact_name": "Ada Maker",
  "contact_phone": "+27 82 123 4567",
  "contact_email": "ada@example.com",
  "contact_note": "WhatsApp only, weekdays 8 to 5",
  "contact_suggestion": null
}
```

Before anyone saves, the four fields are `""`. Editors still receive `contact_suggestion` so the page can prefill the inputs. Collectors see `contact_suggestion: null` and, until a save, no contact on the forms.

### Read one form, and the project form list

`GET /api/forms/3f1c2a40-1111-4b2a-9c0d-a1b2c3d4e5f6/`

`GET /api/projects/aa0e1b22-3333-4c4d-8e5f-60718293a4b5/forms/`

`contact` is read-only. It is the same object on every form in the project. It is `null` when all four stored fields are blank.

```json
{
  "id": "3f1c2a40-1111-4b2a-9c0d-a1b2c3d4e5f6",
  "project": "aa0e1b22-3333-4c4d-8e5f-60718293a4b5",
  "title": "Household survey",
  "contact": {
    "name": "Ada Maker",
    "phone": "+27 82 123 4567",
    "email": "ada@example.com",
    "note": "WhatsApp only, weekdays 8 to 5"
  },
  "status": "published"
}
```

The form list returns that same `contact` on each form. The project is already loaded with the list, so this does not add a query per form.

### Clear

`PATCH /api/projects/aa0e1b22-3333-4c4d-8e5f-60718293a4b5/`

```json
{
  "contact_name": "",
  "contact_phone": "",
  "contact_email": "",
  "contact_note": ""
}
```

`200 OK`, and all four fields come back as `""`. Form reads then return `contact: null`.

### Validation errors

`400 Bad Request`. The body is the usual field error object.

Bad phone (`12345`, letters, a dot, a `+` that is not leading, or fewer than 7 / more than 15 digits):

```json
{
  "contact_phone": [
    "Enter a phone number with 7 to 15 digits."
  ]
}
```

A phone that contains anything other than digits, spaces, hyphens, brackets, and one leading `+`:

```json
{
  "contact_phone": [
    "Use digits, spaces, hyphens or brackets, with an optional leading +."
  ]
}
```

Bad email:

```json
{
  "contact_email": [
    "Enter a valid email address."
  ]
}
```

Name or note with neither phone nor email, including a partial update that would leave the project in that state:

```json
{
  "non_field_errors": [
    "Add a phone number or email so collectors can reach this contact."
  ]
}
```

A collector, or anyone else who can read the project but cannot edit its settings:

`403 Forbidden`

```json
{
  "detail": "You do not have permission to change this project."
}
```

The stored contact is left unchanged.

## Mobile

Collectors read one contact for the whole project. It is on every form they already sync, and on the form download. There is no separate messaging API, and `contact_suggestion` is not in these responses.

Read `contact` on `available`, on `GET /api/forms/<id>/`, and on `download`. The shape is `{"name", "phone", "email", "note"}`, or `null`. It is not part of the question schema. A change to contact details does not change `checksum` or `force_update`, so a client that skips a download when the checksum matches will keep a stale phone number.

Every form in the project returns the same `contact`.

### Logged-in collector: available forms

`GET /api/forms/available/`

`Authorization: Bearer <access_token>`

```json
[
  {
    "id": "3f1c2a40-1111-4b2a-9c0d-a1b2c3d4e5f6",
    "title": "Household survey",
    "contact": {
      "name": "Ada Maker",
      "phone": "+27 82 123 4567",
      "email": "ada@example.com",
      "note": "WhatsApp only, weekdays 8 to 5"
    },
    "published_checksum": "ab12…",
    "force_update": true
  },
  {
    "id": "9c0d1e2f-2222-4a3b-8c4d-5e6f708192a3",
    "title": "Follow-up survey",
    "contact": {
      "name": "Ada Maker",
      "phone": "+27 82 123 4567",
      "email": "ada@example.com",
      "note": "WhatsApp only, weekdays 8 to 5"
    },
    "published_checksum": "cd34…",
    "force_update": true
  }
]
```

A project with no contact still includes the key, set to `null`, on every form.

### Logged-in collector: download

`GET /api/forms/3f1c2a40-1111-4b2a-9c0d-a1b2c3d4e5f6/download/`

`contact` is a top-level key beside `questions`, `checksum`, and `force_update`. It is not inside `questions`, and it is not inside the stored schema.

```json
{
  "formId": "3f1c2a40-1111-4b2a-9c0d-a1b2c3d4e5f6",
  "title": "Household survey",
  "checksum": "ab12…",
  "force_update": true,
  "questions": [],
  "contact": {
    "name": "Ada Maker",
    "phone": "+27 82 123 4567",
    "email": "ada@example.com",
    "note": "WhatsApp only, weekdays 8 to 5"
  }
}
```

When all four stored fields are blank, `contact` is `null`:

```json
{
  "formId": "3f1c2a40-1111-4b2a-9c0d-a1b2c3d4e5f6",
  "checksum": "ab12…",
  "force_update": true,
  "contact": null
}
```

`checksum` remains the hash of the question schema only. Do not hash `contact` into it.

### Logged-out caller, including a demo form

`GET /api/forms/available/` and `GET /api/forms/<form_id>/download/` stay open for demo forms. Contact details are still hidden. `contact` is `null`, including when the project has a saved contact.

```json
[
  {
    "id": "3f1c2a40-1111-4b2a-9c0d-a1b2c3d4e5f6",
    "title": "Demo survey",
    "contact": null
  }
]
```

```json
{
  "formId": "3f1c2a40-1111-4b2a-9c0d-a1b2c3d4e5f6",
  "title": "Demo survey",
  "checksum": "ab12…",
  "force_update": true,
  "contact": null
}
```

Do not show a contact row in that case. The value is withheld, not missing because nobody saved a contact.
