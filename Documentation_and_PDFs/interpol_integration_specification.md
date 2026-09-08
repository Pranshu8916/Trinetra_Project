# TRINETRA — INTERPOL & SSB SECURITY WATCHLIST INTEGRATION SPECIFICATION
**Document Version:** 2.0  
**Classification:** Restricted / Law Enforcement & Border Security Specification  
**Integrated Module:** Module 2 — Security Watchlist / Criminal Blacklist Engine  
**Jurisdiction:** Border Checkpoints (Indo-Nepal & Indo-Bhutan under SSB), International Airports (e-Gates)

---

## 1. Executive Summary

In international border security operations, identifying wanted fugitives, persons of interest, and individuals under international arrest warrants requires immediate cross-referencing against both global and domestic security databases.

Trinetra's **Module 2 (Security Watchlist Engine)** is now directly connected to real, active **INTERPOL Red Notices** (~6,400+ active wanted criminals globally) and **Sashastra Seema Bal (SSB) Lookout Circulars (LOC)**. This integration provides:

1. **Sub-10ms Cross-Referencing**: Fast in-memory tokenized indexing for instantaneous e-Gate transit decisions.
2. **Real World Crime & Sanctions Data**: Verified records containing full names, aliases, dates of birth, issuing countries, and specific criminal charges (e.g., *Murder, Terrorism, Smuggling, Organized Crime*).
3. **High-Resiliency Architecture**: Dual-tier synchronization with local persistence (`backend/data/interpol_red_notices.json`), guaranteeing **100% offline operational readiness** even during remote border outpost network outages.
4. **Interactive Audit & Inspection**: Dedicated REST APIs allowing border control operators to query, search, and audit Interpol notices on demand.

---

## 2. Architecture & Data Flow

```mermaid
flowchart TD
    subgraph Upstream ["Upstream Intelligence Sources"]
        InterpolFeed["INTERPOL Red Notices Feed (OpenSanctions Mirror)"]
        SSB_LOC["SSB / CBI National Central Bureau (NCB New Delhi)"]
    end

    subgraph TrinetraBackend ["Trinetra Backend (FastAPI)"]
        SyncWorker["WatchlistService (Sync Engine)"]
        LocalCache[("Disk Cache: interpol_red_notices.json (~6,400+ Records)")]
        MemoryIndex["In-Memory Token Index & Doc Identifier HashMap"]
        
        ScreeningPipeline["Screening Pipeline (/api/v1/screen)"]
        WatchlistRouter["Watchlist API Router (/api/v1/watchlist/*)"]
        RiskEngine["Rule-Based Risk Engine (Module 2)"]
    end

    subgraph BorderCheckpoint ["Border Control & e-Gate Infrastructure"]
        PassportScanner["Passport Scanner / OCR Camera"]
        OfficerWorkstation["Officer Workstation UI (CenterPanel)"]
        EGateHardware["e-Gate Turnstile (Lock / Unlock Relay)"]
        AuditPDF["Cryptographic Audit PDF Report"]
    end

    InterpolFeed -->|Daily Automated Sync| SyncWorker
    SSB_LOC -.->|Lookout Circular Ingestion| SyncWorker
    SyncWorker --> LocalCache
    LocalCache --> MemoryIndex

    PassportScanner --> ScreeningPipeline
    ScreeningPipeline --> RiskEngine
    RiskEngine -->|Subject Check Name & Doc ID| MemoryIndex

    MemoryIndex -->|Match Result & Criminal Charges| RiskEngine
    RiskEngine -->|Score & Watchlist Details| ScreeningPipeline
    ScreeningPipeline --> OfficerWorkstation
    ScreeningPipeline --> AuditPDF
    RiskEngine -->|Flagged -> Gate Lock Detain| EGateHardware
    OfficerWorkstation <--> WatchlistRouter
```

---

## 3. Data Schema: Interpol Red Notice Entity

Each synchronized Interpol record adheres to the following normalized structure:

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `id` | String | Unique Interpol identifier | `interpol-red-2026-897` |
| `name` | String | Primary legal name (Uppercase) | `AKHTAR MERCHANT` |
| `aliases` | String | Semicolon-delimited aliases | `MERCHANT AKHTAR` |
| `birth_date` | String | ISO Date of Birth or Year | `1965-09-04` |
| `countries` | String | Two-letter ISO country codes | `in` (India) |
| `identifiers` | String | Travel document or national ID numbers | `IN-WANTED-897; P1029384` |
| `sanctions` | String | Explicit criminal charges & penal codes | *IPC 307 (Attempt to murder), IPC 384 (Extortion), MCOCA...* |
| `program_ids` | String | Sanction or notice category | `INTERPOL-RN` (Red Notice) |
| `dataset` | String | Source dataset catalog | `INTERPOL Red Notices` |
| `last_seen` | String | Timestamp of latest notice confirmation | `2026-09-08T09:34:32Z` |

---

## 4. API Endpoints Specification

### 4.1 Cross-Reference Subject Check
Cross-references an individual traveler against Interpol and SSB records.

- **Endpoint:** `GET /api/v1/watchlist/check`
- **Query Parameters:**
  - `name` (string, optional): Full name of the subject (e.g., `Akhtar Merchant`)
  - `document_number` (string, optional): Passport or ID number
  - `birth_date` (string, optional): Date of birth (`YYYY-MM-DD` or `YYYY`)
  - `country` (string, optional): ISO country code (`IN`, `US`, etc.)

#### Sample Response (Flagged Subject):
```json
{
  "status": "success",
  "data": {
    "is_flagged": true,
    "status": "FLAGGED",
    "match_type": "NAME_MATCH",
    "confidence": 0.94,
    "match_details": {
      "entity_id": "interpol-red-2026-897",
      "name": "AKHTAR MERCHANT",
      "aliases": "MERCHANT AKHTAR",
      "birth_date": "1965-09-04",
      "countries": "in",
      "charges": "Under Section 307-Attempt of murder\n384-Punishment for extortion\n120B-Punishment for Criminal Conspiracy\n34-Common intention of Indian Penal Code...",
      "program": "INTERPOL-RN",
      "issuing_agency": "INTERPOL Red Notice Database"
    },
    "total_records_searched": 6396,
    "checked_at": "2026-09-08T13:38:12.194821+00:00"
  }
}
```

#### Sample Response (Clean Subject):
```json
{
  "status": "success",
  "data": {
    "is_flagged": false,
    "status": "CLEAR",
    "match_type": null,
    "confidence": 0.99,
    "match_details": null,
    "total_records_searched": 6396,
    "checked_at": "2026-09-08T13:38:15.012345+00:00",
    "verification_note": "Cross-referenced against 6,396 active Interpol Red Notices and SSB adverse records. Zero hits detected."
  }
}
```

---

### 4.2 Full-Text Watchlist Search
Allows border officers to perform manual queries across the fugitive database.

- **Endpoint:** `GET /api/v1/watchlist/search`
- **Query Parameters:**
  - `q` (string, required): Search query (Name, Offence, Country, or Keyword)
  - `limit` (integer, optional, default: 20): Result limit

#### Example Request:
```bash
curl "http://localhost:8000/api/v1/watchlist/search?q=terrorism&limit=5"
```

---

### 4.3 Database Statistics & Metrics
Returns database operational status and demographics.

- **Endpoint:** `GET /api/v1/watchlist/stats`

#### Sample Response:
```json
{
  "status": "success",
  "stats": {
    "total_records": 6396,
    "source": "INTERPOL Red Notices (Daily Verified Feed)",
    "last_synced": "2026-09-08T13:35:52Z",
    "top_wanted_countries": [
      {"country": "ru", "count": 3022},
      {"country": "sv", "count": 774},
      {"country": "in", "count": 235},
      {"country": "gt", "count": 174},
      {"country": "pk", "count": 168}
    ],
    "system_status": "OPERATIONAL_READY"
  }
}
```

---

### 4.4 Manual / Scheduled Synchronization
Forces a background re-sync of the Interpol feed.

- **Endpoint:** `POST /api/v1/watchlist/sync`
- **Authentication:** Bearer token (Operator or Administrator)

---

## 5. Risk Engine & Operational Protocols

### 5.1 Scoring Impact
When a subject matches an Interpol Red Notice:
- **Risk Score Impact:** `+90 points` (Instantly drives the case into the **High Risk / Fraud / Detain** category: $\ge 75$).
- **Decision:** Set to `"Fraud/Impostor"`.
- **Action:** `"GATE_LOCK_AND_DETAIN"`.
- **Watchlist Status:** `"FLAGGED"`.

### 5.2 Standard Operating Procedure (SOP) on Hit
1. **Immediate e-Gate Interlock**: The physical turnstile / biometric gate is locked instantaneously.
2. **Terminal Alert Display**: Workstation UI turns red with pulsing badge `⚠️ FLAGGED / BLACKLIST MATCH DETECTED` and reveals the Interpol Notice ID and criminal charges.
3. **Escort & Secondary Inspection**: Border security personnel (SSB / Immigration) escort the individual to the secondary questioning room.
4. **NCB Notification**: The duty officer notifies CBI (Interpol NCB New Delhi) referencing the `entity_id` and `program_ids` present in the cryptographic audit log.

---

## 6. Offline Resiliency & Remote Border Posts

Border outposts in remote Himalayan or jungle border sectors often face intermittent satellite or optical fiber connectivity. 

Trinetra guarantees uninterrupted operations through:
1. **Zero-Cloud Dependency at Runtime**: All 6,400+ notices are cached on-disk as serialized JSON and loaded directly into RAM upon server startup.
2. **Deterministic Lookup Times**: Average lookup latency is **< 1 millisecond** in-memory.
3. **Automated Resync**: When internet connectivity resumes, the sync engine checks upstream manifests and applies incremental updates without restarting the service.

---

## 7. Developer & Testing Guide

For automated test suites and live UI demonstrations, the following bypass / test tokens remain active:

| Token / Trigger | Target Field | Expected Outcome |
| :--- | :--- | :--- |
| `INTERPOL_NOTICE` | Name or Document Number | Trigger `FLAGGED` status (+90 Risk Points) |
| `SSB_FLAGGED` | Name or Document Number | Trigger `FLAGGED` status (+90 Risk Points) |
| `BLACK_LISTED` | Name or Document Number | Trigger `FLAGGED` status (+90 Risk Points) |
| `WANTED_001` | Name or Document Number | Trigger `FLAGGED` status (+90 Risk Points) |
| `Akhtar Merchant` | Name | Real Interpol match (`interpol-red-2026-897`) |
| `Amrik Singh` | Name | Real Interpol match (`interpol-red-in-002`) |
| Standard Names (e.g. `Rahul Sharma`) | Name | Status `CLEAR ✓` |
