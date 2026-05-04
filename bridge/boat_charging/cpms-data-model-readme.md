# Data Model & API Overview CPMS

This document explains the core data hierarchy exposed through the Evinity CPMS Locations API: how locations,
tariffs, charging stations, and EVSEs relate to each other, and which endpoints to use to retrieve them.

---

## Data Hierarchy

The data is organized in a four-level hierarchy:

```
Location
  │
  ├── Tariff  (one tariff per location, referenced by tariffId)
  │
  └── ChargingStation  (one or many per location)
        │
        └── EVSE  (one or many per charging station)
              │
              └── Connector  (one or many per EVSE)
```

### Level 1 — Location

A **Location** is a physical place (a marina berth, dock, or pier) where charging infrastructure
is installed. It carries address, coordinates, operator info, opening times, and a reference to
its pricing tariff.

Key fields:

| Field                  | Type       | Description                                         |
|------------------------|------------|-----------------------------------------------------|
| `id`                   | string     | Unique identifier                                   |
| `name`                 | string     | Human-readable name of the location                 |
| `address`              | string     | Street address                                      |
| `city`                 | string     | City                                                |
| `postalCode`           | string     | Postal code                                         |
| `country`              | string     | Country code (e.g. `NL`)                            |
| `coordinates`          | object     | `{ latitude, longitude }`                           |
| `parkingType`          | string     | Type of parking (e.g. `ON_STREET`, `PARKING_LOT`)  |
| `openingTimes`         | object     | `{ twentyfourseven: true/false }`                   |
| `chargingWhenClosed`   | boolean    | Whether charging is allowed outside opening times   |
| `operator`             | object     | `{ name, website }` — the operator of the location  |
| `tariffId`             | string     | **Foreign key** — links this location to its Tariff |
| `chargingStationsIds`  | string[]   | List of IDs of all charging stations at this location |
| `availableSockets`     | number     | Count of currently available sockets                |
| `totalSockets`         | number     | Total socket count across all stations              |
| `lastUpdated`          | string     | ISO 8601 datetime of last data change               |

---

### Level 2 — Tariff

A **Tariff** defines the pricing structure applied to all charging sessions at a location.
Every location references exactly one tariff via its `tariffId`.

Key fields:

| Field                        | Type   | Description                                         |
|------------------------------|--------|-----------------------------------------------------|
| `id`                         | string | Unique identifier                                   |
| `name`                       | string | Display name for the tariff                         |
| `currency`                   | string | ISO 4217 currency code (e.g. `EUR`)                 |
| `energyPricePerKwh`          | number | Price per kWh of energy consumed                    |
| `chargingTimePricePerHour`   | number | Optional: price per hour the vehicle is charging    |
| `parkingTimePricePerHour`    | number | Optional: price per hour the vehicle occupies a spot|
| `flatFeePrice`               | number | Optional: one-time session start fee                |

> **Relationship**: `Location.tariffId` → `Tariff.id`  (many locations can share one tariff)

---

### Level 3 — Charging Station

A **Charging Station** is a physical device installed at a location.
One location can have multiple stations. Each station reports its own connection status and
hardware attributes.

Key fields:

| Field            | Type    | Description                                              |
|------------------|---------|----------------------------------------------------------|
| `id`             | string  | Unique identifier                                        |
| `locationId`     | string  | **Foreign key** — links back to the parent Location      |
| `availability`   | string  | Overall availability: `AVAILABLE`, `OCCUPIED`, `FAULTED` |
| `status`         | string  | Current operational status                               |
| `protocol`       | string  | Communication protocol (e.g. `OCPP1.6`, `OCPP2.0`)      |
| `accepted`       | boolean | Whether the station has been accepted/registered          |
| `reservable`     | boolean | Whether it can be reserved in advance                    |
| `blocked`        | boolean | Whether the station is administratively blocked          |
| `lastSeen`       | string  | ISO 8601 datetime of last heartbeat from the station     |
| `evses`          | array   | List of EVSEs (sockets) on this station                  |

> **Relationship**: `Location.chargingStationsIds[]` contains `ChargingStation.id`

---

### Level 4 — EVSE (Electric Vehicle Supply Equipment)

An **EVSE** represents one charging outlet (socket) on a charging station. A single charging
station can have one or more EVSEs — each EVSE charges one vehicle at a time.

Key fields:

| Field          | Type   | Description                                                     |
|----------------|--------|-----------------------------------------------------------------|
| `id`           | number | Internal row identifier                                         |
| `evseId`       | string | Human-readable EVSE identifier (e.g. `BE-BEC-E041503003-0`)    |
| `ocppEvseId`   | number | EVSE number used in the OCPP protocol                           |
| `status`       | string | Current status: `AVAILABLE`, `CHARGING`, `RESERVED`, `FAULTED` |
| `availability` | string | Configured availability (can differ from live status)           |
| `connectors`   | array  | List of physical connectors on this EVSE                        |

> **Relationship**: `ChargingStation.evses[]` (embedded array within the station object)

---

### Level 4b — Connector

A **Connector** is the physical plug/socket within an EVSE. Most EVSEs have one connector,
though some have two (e.g. one Type 2 cable + one CCS socket).

Key fields:

| Field               | Type   | Description                                              |
|---------------------|--------|----------------------------------------------------------|
| `connectorId`       | number | Connector number on the EVSE (usually 1-based)           |
| `connectorType`     | string | Plug standard: `Type2`, `CCS`, `CHAdeMO`, `Schuko`, etc. |
| `current`           | string | Current type: `AC` or `DC`                              |
| `voltage`           | number | Voltage in volts (e.g. `230`, `400`)                    |
| `maxAmp`            | number | Maximum amperage                                         |
| `maxElectricPower`  | number | Maximum power in watts (e.g. `22000` = 22 kW)           |
| `status`            | string | Current status of this specific connector                |

> **Relationship**: `EVSE.connectors[]` (embedded array within the EVSE object)

---

## Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              LOCATION                                   │
│                                                                         │
│  id · name · address · city · country · coordinates                     │
│  parkingType · openingTimes · operator · lastUpdated                    │
│  availableSockets · totalSockets                                        │
│                                                                         │
│  tariffId ──────────────────────────────────────────────┐              │
│  chargingStationsIds[]  ──────────────────────────┐     │              │
└───────────────────────────────────────────────────│─────│──────────────┘
                                                    │     │
                          ┌─────────────────────────┘     │
                          │                               │
                          ▼                               ▼
         ┌─────────────────────────┐       ┌─────────────────────┐
         │    CHARGING STATION     │       │       TARIFF         │
         │                         │       │                     │
         │  id · locationId        │       │  id · currency      │
         │  availability · status  │       │  energyPricePerKwh  │
         │  protocol · lastSeen    │       │  flatFeePrice       │
         │  reservable · blocked   │       │  chargingTime...    │
         │                         │       │  parkingTime...     │
         │  evses[] ──────────┐    │       └─────────────────────┘
         └────────────────────│────┘
                              │
                              ▼
                 ┌────────────────────────┐
                 │          EVSE          │
                 │                        │
                 │  id · evseId           │
                 │  ocppEvseId · status   │
                 │  availability          │
                 │                        │
                 │  connectors[] ─────┐   │
                 └───────────────────│───┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │       CONNECTOR        │
                        │                        │
                        │  connectorId · type    │
                        │  current · voltage     │
                        │  maxAmp · maxPower     │
                        │  status                │
                        └────────────────────────┘
```

**Cardinalities at a glance:**

| Relationship                       | Type      |
|------------------------------------|-----------|
| Location → Tariff                  | Many → One (many locations can share one tariff) |
| Location → Charging Station        | One → Many                                       |
| Charging Station → EVSE            | One → Many                                       |
| EVSE → Connector                   | One → Many (usually one)                         |

---

## API Endpoints

All paginated list endpoints return a standard page wrapper:

```json
{
  "content": [ ... ],
  "totalElements": 42,
  "totalPages": 3,
  "number": 0,
  "numberOfElements": 20,
  "first": true,
  "last": false
}
```

### Locations

| Method | Path              | Description                                      |
|--------|-------------------|--------------------------------------------------|
| GET    | `/locations`      | Paginated list of locations                      |
| GET    | `/locations/{id}` | Single location                                  |

**Query parameters for `/locations`:**

| Parameter | Default     | Description                                 |
|-----------|-------------|---------------------------------------------|
| `page`    | `0`         | Zero-based page index                       |
| `size`    | `20`        | Number of results per page                  |
| `sort`    | `name,asc`  | Sort field and direction (e.g. `city,desc`) |
| `filter`  | —           | Filter expression (see below)               |

### Tariffs

| Method | Path             | Description           |
|--------|------------------|-----------------------|
| GET    | `/tariffs`       | Paginated list of tariffs |
| GET    | `/tariffs/{id}`  | Single tariff by ID       |

### Charging Stations

| Method | Path                         | Description                    |
|--------|------------------------------|--------------------------------|
| GET    | `/charging-stations`         | Paginated list of stations     |

---

## Filter Syntax

Several endpoints accept a `filter` query parameter using a custom expression language:

| Operator | Meaning       | Example                                  |
|----------|---------------|------------------------------------------|
| `≡`      | Exact match   | `id≡'loc-123'`                           |
| `≈`      | Contains      | `name≈'%amsterdam%'`                     |
| `∧`      | AND           | `(city≡'Amsterdam'∧publish≡true)`        |
| `∨`      | OR            | `(id≡'a'∨id≡'b')`                        |

Expressions can be nested: `((city≡'Amsterdam')∧(publish≡true))`

For case-insensitive text search: `lower(name)≈'%test%'`

---

## Session Management (CPMS)

These two endpoints instruct the CPMS to start or stop a charging transaction on a specific
station and EVSE.

### POST `/operator-api/charging-stations/{stationId}/start-transaction`

Starts a charging session on the given station and EVSE.

**Path parameter:**

| Parameter   | Type   | Description                    |
|-------------|--------|--------------------------------|
| `stationId` | string | ID of the charging station     |

**Request body:**

```json
{
  "evseId": "SOME-EVSE-ID",
  "identifyingToken": {
    "token": "SOME-TOKEN-ID"
  }
}
```

| Field                       | Type   | Description                                        |
|-----------------------------|--------|----------------------------------------------------|
| `evseId`                    | string | The EVSE identifier to charge on (`evse.evseId`)   |
| `identifyingToken.token`    | string | Authorization token used to identify the session   |

---

### POST `/operator-api/charging-stations/{stationId}/stop-transaction`

Stops the active charging transaction on the given station.

**Path parameter:**

| Parameter   | Type   | Description                    |
|-------------|--------|--------------------------------|
| `stationId` | string | ID of the charging station     |

**Request body:**

```json
{
  "id": "transaction-id-from-cpms"
}
```

| Field | Type   | Description                                                       |
|-------|--------|-------------------------------------------------------------------|
| `id`  | string | The CPMS transaction ID to stop (obtained after start-transaction)|
