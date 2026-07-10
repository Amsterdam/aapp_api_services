# Amsterdam Boat — Mobile App API Integration Guide

**Version:** 1.0
**Date:** 2026-05-03
**Audience:** Mobile app developer

---

## Overview

The Amsterdam Boat backend provides a REST API for browsing charging locations and managing charging sessions with iDEAL payments. The mobile app will share the same backend and user accounts as the existing web app — users will see the same sessions and use the same login on both platforms.

This document covers everything needed to integrate the mobile app with the API. The attached **session-states.drawio** diagram provides a visual reference for the session state machine described in this document.

**Base URL:** `https://amsboatapp-tst.nrganext.nl/api`
**Swagger UI:** `https://amsboatapp-tst.nrganext.nl/api/swagger` — select **Client API v1**

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Payment Redirect — Action Required](#2-payment-redirect--action-required)
3. [Session Lifecycle](#3-session-lifecycle)
4. [Endpoint Reference — Locations](#4-endpoint-reference--locations)
5. [Endpoint Reference — Sessions](#5-endpoint-reference--sessions)
6. [Rate Limiting](#6-rate-limiting)
7. [Error Handling](#7-error-handling)
8. [Recommended Mobile Flow](#8-recommended-mobile-flow)
9. [Open Questions](#9-open-questions)

---

## 1. Authentication

The mobile app shares the same **AWS Cognito User Pool** as the web app. A new Cognito **App Client** will be created for the mobile app — we will provide you with the Client ID. The User Pool ID and region stay the same.

### Obtaining a token

Use the AWS Amplify SDK, AWS SDK, or Cognito hosted UI to authenticate the user and obtain an **access token** (JWT).

### Sending the token

Include the access token as a Bearer token in the `Authorization` header on every request:

```
Authorization: Bearer <access_token>
```

Tokens are validated against Cognito's public keys on the backend. No audience validation is enforced.

### Authentication requirements per endpoint

| Endpoint | Token required? | Behavior |
|----------|----------------|----------|
| `GET /locations`, `GET /locations/pins`, `GET /locations/{id}` | No | Fully public. No authentication needed. |
| `GET /sessions` | **Yes** | Returns all sessions for the authenticated user. Returns 401 without a token. |
| `GET /sessions/{id}` | Recommended | With token: ownership enforced (403 if not yours). Without: accessible by UUID. |
| `POST /sessions` | Recommended | With token: email is taken from the JWT (request body `email` is ignored). Without: guest flow using the request body email. |
| `POST /sessions/{id}/start` | Recommended | With token: ownership enforced. Without: accessible by UUID. |
| `POST /sessions/{id}/stop` | Recommended | With token: ownership enforced. Without: accessible by UUID. |

**Important:** Always send the Bearer token from the mobile app. This ensures:
- Sessions are linked to the user's account (visible in `GET /sessions`)
- Other users cannot access, start, or stop the session (ownership enforcement returns 403)
- The user's email is securely taken from the JWT, not from user input

---

## 2. Payment Redirect — Action Required

When a session is created via `POST /sessions`, the API returns a `checkoutUrl` pointing to the Worldline/iDEAL payment page. After the user completes the payment, Worldline redirects the user back to a **return URL**.

Currently, this return URL points to the **web app frontend** (e.g. `https://amsboatapp-tst.nrganext.nl/sessions/{uniqueId}`). For the mobile app, this redirect needs to go back to the mobile app instead.

### What we need from you

Please provide the return URL format that the mobile app can handle after payment. The two common approaches are:

**Option A — Universal Links / App Links (recommended)**
```
https://amsboatapp-tst.nrganext.nl/sessions/{uniqueId}
```
The mobile OS intercepts this URL and opens the app directly. Falls back to the browser if the app is not installed. Requires server-side configuration (`.well-known/assetlinks.json` for Android, `apple-app-site-association` for iOS).

**Option B — Custom URL Scheme**
```
amsterdamboat://sessions/{uniqueId}
```
Simpler to set up, but does not work if the app is not installed (no browser fallback). Some payment providers may not accept custom schemes as return URLs.

### How it will work

Once you provide the return URL format, we will update the backend so that the mobile app can pass its return URL when creating a session. The web app will continue using the existing redirect. The `POST /sessions` request body will accept an optional `returnUrl` field:

```json
{
  "stationId": "CS-001",
  "socketNumber": "1",
  "name": "Jan",
  "email": "jan@example.com",
  "returnUrl": "https://yourdomain.com/app/sessions"
}
```

The backend will validate this URL against an allowlist of approved redirect origins to prevent open redirect attacks.

---

## 3. Session Lifecycle

A charging session goes through the following states. See the attached **session-states.drawio** diagram for the full visual reference including background/automatic transitions.

### States

| Status | Name | Description |
|--------|------|-------------|
| 1 | **Created** | Payment checkout URL generated. Awaiting iDEAL payment. |
| 2 | **CheckedOut** | Payment pre-authorized. Ready to start charging. |
| 3 | **Charging** | CPMS session active. Boat is drawing power. TransactionId assigned. |
| 4 | **Completed** | Charging finished. Payment captured for actual usage. *Terminal state.* |
| 5 | **Cancelled** | Expired or user never completed payment. Refunded if pre-auth was taken. *Terminal state.* |

### Happy path

```
Step 1:  POST /sessions              →  Status 1 (Created)
         Response: { "checkoutUrl": "https://payment.worldline.com/..." }

Step 2:  Open checkoutUrl in in-app browser (iDEAL payment page)

Step 3:  User completes payment, app regains control

Step 4:  GET /sessions/{id}          →  Status auto-promotes 1 → 2 (CheckedOut)
         (backend checks payment status with Worldline on every GET)

Step 5:  POST /sessions/{id}/start   →  Status 2 → 3 (Charging)

Step 6:  POST /sessions/{id}/stop    →  Status 3 → 4 (Completed)
```

### Timing and behavior notes

| Situation | What happens |
|-----------|-------------|
| **Starting charge (step 5)** | The backend sends an OCPP command to the physical charger. This can take up to **1 minute**. Show a loading/spinner state. |
| **Stopping charge (step 6)** | Same — up to **1 minute** for the charger to confirm.  |
| **Session idle > 20 min in status 1 or 2** | Automatically cancelled (status 5) by the background cleanup service. If payment was pre-authorized, it is refunded. |
| **Charging session exceeds 24 hours** | Force-stopped with a standard fine applied. |
| **Budget overrun (cost > 90% of pre-auth)** | Automatically stopped and payment captured. |
| **Cable unplugged during charge** | Detected by the charger management system. Session is finalized and payment captured. |

---

## 4. Endpoint Reference — Locations

All location endpoints are fully public. No authentication is needed.

### `GET /locations`

Returns a paginated list of charging station locations.

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 0 | Zero-based page index |
| `size` | int | 20 | Items per page |
| `sort` | string | `name,asc` | Sort expression (e.g. `name,asc`, `name,desc`) |
| `filter` | string | — | Optional free-text search filter |

### `GET /locations/pins`

Returns a minimal list of all locations with only the fields needed for map markers: id, name, and coordinates. Use this for the map overview screen.

### `GET /locations/{id}`

Returns full details of a single location, including address, tariff information, charging stations, connectors, and real-time socket availability.

**Response example:**
```json
{
  "id": "LOC-001",
  "name": "Prinsengracht Laadpunt",
  "address": "Prinsengracht 100",
  "city": "Amsterdam",
  "postalCode": "1015 DV",
  "coordinates": { "latitude": "52.3676", "longitude": "4.8837" },
  "openingTimes": { "twentyfourseven": true },
  "availableSockets": 2,
  "totalSockets": 4,
  "chargingStations": [ ... ],
  "tariff": { ... }
}
```

---

## 5. Endpoint Reference — Sessions

### `POST /sessions`

Creates a payment checkout session for a specific charging socket. Returns the Worldline checkout URL.

**Rate limited:** 10 requests per minute.

**Request body:**
```json
{
  "stationId": "CS-001",
  "socketNumber": "1",
  "name": "Jan de Boer",
  "email": "jan@example.com"
}
```

| Field | Type | Max length | Description |
|-------|------|------------|-------------|
| `stationId` | string | 100 | CPMS charging station identifier (from location details). Required. |
| `socketNumber` | string | 10 | EVSE / socket number on the station. Required. |
| `name` | string | 200 | User display name. Only used for guest confirmation emails. Required. |
| `email` | string | 320 | User email, must be valid format. **Ignored when a Bearer token is provided** — the email from the JWT is used instead. Required. |

**Deduplication:** If an identical request (same stationId + socketNumber + email) is received within 10 seconds and the first session is still in status 1, the existing checkout URL is returned instead of creating a duplicate. This protects against double-taps and network retries.

**Response (200):**
```json
{
  "checkoutUrl": "https://payment.worldline.com/checkout/..."
}
```

Open this URL in an in-app browser or WebView for the user to complete the iDEAL payment.

**Errors:**

| Status | Meaning |
|--------|---------|
| 400 | Invalid request body (missing required fields, invalid email format, exceeds max length) |
| 500 | PreAuthorizationAmount is not configured (server issue) |
| 502 | Failed to create checkout with payment provider |

---

### `GET /sessions`

Returns all sessions for the authenticated user, ordered by most recent first. Each session includes CPMS charging data and location details when available.

**Requires Bearer token.** Returns 401 without one.

**Response (200):**
```json
[
  {
    "session": {
      "uniqueId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "stationId": "CS-001",
      "socketNumber": "1",
      "status": 3,
      "desiredAmount": 50.0,
      "finalAmount": 0.0,
      "createdAt": "2026-05-03T10:30:00Z",
      "locationId": "LOC-001"
    },
    "cpmsSession": {
      "startDateTime": "2026-05-03T10:35:00Z",
      "kwh": 12.5,
      "status": "ACTIVE",
      "totalCost": { "exclVat": 6.25 }
    },
    "location": {
      "id": "LOC-001",
      "name": "Prinsengracht Laadpunt",
      "address": "Prinsengracht 100",
      "city": "Amsterdam",
      "coordinates": { "latitude": "52.3676", "longitude": "4.8837" }
    }
  }
]
```

**Fields of note:**
- `session.status` — see [Session Lifecycle](#3-session-lifecycle) for status codes
- `session.desiredAmount` — the pre-authorization amount (EUR)
- `session.finalAmount` — the actual captured amount after charging completes (EUR, 0.0 until status 4)
- `cpmsSession` — live charging data from the charger management system (null if charging hasn't started)
- `cpmsSession.kwh` — energy delivered so far
- `cpmsSession.totalCost.exclVat` — running cost excluding VAT
- `location` — the charging location details (null if location data is unavailable)

**Errors:**

| Status | Meaning |
|--------|---------|
| 401 | Missing or invalid Bearer token |
| 404 | User account not found in the database |

---

### `GET /sessions/{id}`

Returns a single session by its public unique identifier (GUID).

If the session is in status 1 (Created) and the payment has been completed, the backend automatically promotes it to status 2 (CheckedOut) before returning the response.

**With a Bearer token:** ownership is enforced — you can only access your own sessions (403 otherwise).

**Response (200):** Same structure as a single item from `GET /sessions`.

**Errors:**

| Status | Meaning |
|--------|---------|
| 403 | Authenticated user does not own this session |
| 404 | Session not found |

---

### `POST /sessions/{id}/start`

Starts the physical charging session on the charger. The session must be in **CheckedOut (2)** state.

This endpoint communicates with the charger via OCPP. **Response time can be up to 3 minutes** — show a loading state in the UI.

**Rate limited:** 10 requests per minute.
**With a Bearer token:** ownership is enforced.

**Request body:** None.

**Response:** `200 OK` (empty body). Session transitions to status 3 (Charging).

**Errors:**

| Status | Meaning |
|--------|---------|
| 400 | Session is not in CheckedOut (2) state |
| 403 | Authenticated user does not own this session |
| 404 | Session not found |
| 502 | Charger not found, CPMS communication failed, or OCPP command rejected |
| 504 | Timed out waiting for the charger to respond. The command may still succeed — poll `GET /sessions/{id}` before retrying. |

---

### `POST /sessions/{id}/stop`

Stops the physical charging session and captures the payment for actual usage. The session must be in **Charging (3)** state.

**Response time can be up to 1 minute.** After stopping, the final amount is calculated as:
`CPMS cost (excl. VAT) x 1.21 (Dutch VAT)`, captured from the pre-authorized amount.

**Rate limited:** 10 requests per minute.
**With a Bearer token:** ownership is enforced.

**Request body:** None.

**Response:** `200 OK` (empty body). Session transitions to status 4 (Completed).

**Errors:**

| Status | Meaning |
|--------|---------|
| 400 | Session is not in Charging (3) state |
| 403 | Authenticated user does not own this session |
| 404 | Session not found |
| 502 | CPMS communication failed or OCPP command rejected |
| 504 | Timed out waiting for the charger to stop. Poll `GET /sessions/{id}` before retrying. |

---

## 6. Rate Limiting

The following endpoints are rate limited to **10 requests per minute** per client IP:

- `POST /sessions`
- `POST /sessions/{id}/start`
- `POST /sessions/{id}/stop`

When the limit is exceeded, the API returns:

```
HTTP/1.1 429 Too Many Requests
```

All other endpoints (GET requests) are not rate limited.

---

## 7. Error Handling

Error responses return a plain text body with a human-readable description:

```
HTTP/1.1 502 Bad Gateway
Content-Type: text/plain

Failed to start CPMS session.
```

### Error patterns and recommended handling

| Status | Meaning | Recommended action |
|--------|---------|-------------------|
| 400 | Invalid request or session in wrong state | Check session status before calling. Do not retry. |
| 401 | Missing or invalid JWT token | Refresh the Cognito token and retry. |
| 403 | Session belongs to another user | Do not retry. This session is not accessible. |
| 404 | Session or resource not found | Do not retry. |
| 429 | Rate limit exceeded | Wait at least 60 seconds before retrying. |
| 500 | Server configuration error | Report to backend team. |
| 502 | Upstream service error (CPMS or Worldline) | Retry after a short delay (e.g. 5 seconds). |
| 504 | Charger did not respond in time | The operation may still complete. Poll `GET /sessions/{id}` to check the current status before retrying the command. |

---

## 8. Recommended Mobile Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  1. Browse locations                  GET /locations/pins        │
│                                       GET /locations/{id}        │
│                                                                  │
│  2. Select station + socket           (from location details)    │
│                                                                  │
│  3. Create session                    POST /sessions             │
│     Response: { checkoutUrl }                                    │
│                                                                  │
│  4. Open iDEAL payment page           Open checkoutUrl in        │
│                                       in-app browser / WebView   │
│                                                                  │
│  5. Payment complete, return to app   (see Section 2 for         │
│                                        redirect setup)           │
│                                                                  │
│  6. Open session details page         GET /sessions/{id}         │
│                                                                  │
│  7. Start charging                    POST /sessions/{id}/start  │
│     Show loading (up to 3 min)                                   │
│                                                                  │
│  8. Show live charging status         Poll GET /sessions/{id}    │
│     Display kWh, cost, duration       (poll every 10-30 seconds) │
│                                                                  │
│  9. User taps "Stop Charging"         POST /sessions/{id}/stop   │
│     Show loading (up to 1 min)                                   │
│                                                                  │
│  10. Show session summary             GET /sessions/{id}         │
│      Display final amount, kWh        (status = 4)               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Session history:** Use `GET /sessions` (requires Bearer token) to display all past and active sessions. This returns the same data the web app shows.

---

## 9. Open Questions

The following items need to be discussed and decided before integration can begin:

### 9.1 Payment redirect URL (blocking)

After completing the iDEAL payment, Worldline redirects the user back to the app. We need to know what URL format your mobile app can handle. See [Section 2](#2-payment-redirect--action-required) for the two options (Universal Links vs Custom URL Scheme). **Please provide your preferred redirect URL format.**

### 9.2 Cognito App Client

We will create a dedicated Cognito App Client for the mobile app and provide you with the Client ID. Please let us know:
- Which authentication flow do you plan to use? (Authorization Code with PKCE is recommended for mobile)
- Do you need the Cognito Hosted UI, or will you build a custom login screen?

### 9.3 Platform

- Which platform(s) are you targeting? (iOS, Android, or both?)
- Which framework? (native, React Native, Flutter, etc.)

This helps us tailor the Cognito App Client configuration (allowed callback URLs, logout URLs, etc.).

---

*Attached: **session-states.drawio** — open with [draw.io](https://app.diagrams.net) (File > Open from Device)*
