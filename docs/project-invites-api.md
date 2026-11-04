# Project invite links

A project owner creates an invite and shares two things: the link, and an 8-character code. Whoever has both can join that project as a collector. They can use an account they already have, or register with the existing sign-up endpoint and then join.

The link only carries the token. The code is never in the URL. The server stores a salted hash of the code and returns the plain code once, in the create response.

Trailing slashes are required.

## Share link

```text
{FRONTEND_URL}/join?invite=<token>
```

`FRONTEND_URL` is the server setting (no trailing slash needed). The create and list responses include the full `share_url`.

The code uses `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` (no `0`, `O`, `1`, `I`, or `L`). Matching ignores case and spaces around the code.

## Owner

Authenticated. The caller needs the project privilege `manage_members` (the owner, or a manager). Send the access token:

```http
Authorization: Bearer <access_token>
```

### Create

`POST /api/projects/<project_id>/invites/`

```json
{
  "max_uses": 25,
  "expires_at": "2026-11-18T12:00:00+02:00",
  "label": "November field team"
}
```

| Field | Required | Notes |
|---|---|---|
| `max_uses` | Yes | Integer from 1 to 1000 |
| `expires_at` | No | Defaults to 7 days from now. Cannot be more than 90 days away |
| `label` | No | Up to 200 characters. Empty string if omitted |

There is no `role` field. Everyone who joins becomes a collector. A `role` sent here is ignored.

`201` response. `code` is only in this response. Store it now; later reads do not return it.

```json
{
  "id": "8f1c2b40-6e0a-4a1e-9c2d-0b7e6a5d4c31",
  "label": "November field team",
  "status": "active",
  "expires_at": "2026-11-18T12:00:00+02:00",
  "max_uses": 25,
  "uses": 0,
  "failed_attempts": 0,
  "created_by": "ada",
  "created_at": "2026-11-11T12:00:00+02:00",
  "share_url": "https://collect.example.com/join?invite=k3p9_token_example",
  "joined": [],
  "code": "K7MNPQ2R"
}
```

`created_by` is the owner's username.

Out of range `expires_at` or `max_uses` is `400` with a field error. A collector gets `403`. A logged-out caller gets `401`.

### List

`GET /api/projects/<project_id>/invites/`

Same fields as create, without `code`, and without the hash. `joined` lists who came in through that invite.

```json
[
  {
    "id": "8f1c2b40-6e0a-4a1e-9c2d-0b7e6a5d4c31",
    "label": "November field team",
    "status": "active",
    "expires_at": "2026-11-18T12:00:00+02:00",
    "max_uses": 25,
    "uses": 1,
    "failed_attempts": 0,
    "created_by": "ada",
    "created_at": "2026-11-11T12:00:00+02:00",
    "share_url": "https://collect.example.com/join?invite=k3p9_token_example",
    "joined": [
      {
        "username": "field_jane",
        "joined_at": "2026-11-11T15:04:00+02:00"
      }
    ]
  }
]
```

`status` is one of `active`, `expired`, `cancelled`, `locked`, `full`. If more than one applies, the order is cancelled, then locked, then expired, then full, then active.

`locked` means 20 wrong codes were tried. The owner makes a new invite. `full` means `uses` has reached `max_uses`.

### Cancel

`POST /api/projects/<project_id>/invites/<invite_id>/cancel/`

No body. `200` with the same object as a list row, `status` `cancelled`. Cancelling again stays cancelled. People who already joined stay on the project. The link stops working.

Removing someone later is the existing member endpoint, not this one:

`DELETE /api/projects/<project_id>/members/<username>/`

## Person joining

These two routes are under `/api/invites/`. They are limited to 30 requests per minute per IP, shared by both routes. Over the limit the response is `429`.

A wrong code, unknown token, expired invite, cancelled invite, locked invite, and full invite all return the same `400`. The body is only:

```json
{"detail": "This invite or code is not valid."}
```

A missing `code` field is a normal validation error. The page should always send `code`.

### Verify

`POST /api/invites/<token>/verify/`

No login. Does not use a slot.

```json
{"code": "k7mnpq2r"}
```

`200` when the code matches and the invite can still take a new collector:

```json
{"valid": true, "project_name": "Harvest survey"}
```

That is the whole body. It does not include members, forms, counts, or the owner's contact details. Show `project_name`, then ask the person to log in or register. Keep the code in memory and send it again on join.

### Join

`POST /api/invites/<token>/join/`

Login required (`Authorization: Bearer <access_token>`). Logged out is `401`.

```json
{"code": "K7MNPQ2R"}
```

A `role` in this body is ignored.

`200` when they are added:

```json
{
  "project_id": "3b1a9c2e-4d55-4f0a-8c11-6e0d2a9b7f44",
  "project_name": "Harvest survey",
  "role": "collector",
  "already_member": false
}
```

If they are already on the project, the same call returns `200` with `already_member: true` and their current `role`. It does not use a slot and does not change their role. This includes a full invite: an owner or manager can open their own link after the slots are gone.

`uses` counts new collectors only.

Someone who joined and was later removed cannot use that same invite again, even with the right code. The generic `400` is returned. A new invite works.

After 20 wrong codes the invite locks. The right code then gets the same `400`.

## Web page

1. Read `invite` from `/join?invite=<token>`.
2. Ask for the code. `POST /api/invites/<token>/verify/` with `{ "code": "..." }`.
3. On `200`, show `project_name`.
4. If they have no account, register with the existing `POST /api/auth/users/` (password plus password retype). Do not send the invite code there.
5. Log in with the existing `POST /api/auth/jwt/create/` (`username`, `password`). Use the `access` token.
6. `POST /api/invites/<token>/join/` with the same code and `Authorization: Bearer <access_token>`.
7. Open project `project_id`. A new collector can load `GET /api/projects/<project_id>/` and `GET /api/projects/<project_id>/forms/` with that token.

Hold the code in the page between verify and join. Do not put it in the query string.

## Mobile

The same two public calls. The app can open the link, or take a pasted token plus the code.

1. `POST /api/invites/<token>/verify/` with the code.
2. If `valid` is true, show `project_name` and continue only if the person confirms.
3. Register or log in with the existing auth endpoints above. Keep the code in app memory, not in a URL and not in the registration body.
4. `POST /api/invites/<token>/join/` with the bearer token and the code.
5. Store `project_id`. Load that project's forms with the existing forms API.

`already_member: true` means send them to the project they already have. Do not create a second membership.

`400` with `This invite or code is not valid.` is the only invite failure. Do not try to tell a wrong code from an expired or full link. Ask them to check the code, or ask the owner for a new link.

`429` means wait and retry. `401` on join means log in again, then send the code again.
