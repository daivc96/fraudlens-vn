# FraudLens VN

MVP public lookup for fraud threat intelligence: bank accounts, phone numbers,
and suspicious URLs. The UI is Vietnamese-first and designed as a thin public
layer in front of MISP or OpenCTI.

> All bundled records are synthetic demo data. Do not treat them as real-world
> allegations.

## Run locally

No build step or dependency install is required.

```bash
python3 -m http.server 4173 --directory dist
```

Open `http://localhost:4173`.

## Test

```bash
npm test
npm run check
```

## Demo searches

| Type | Value |
| --- | --- |
| Bank account | `0123456789` |
| Phone number | `0901234567` |
| URL | `giaohang-demo.example` |

## Architecture

```text
Collector / analyst intake
          |
          v
Review + normalization service
          |
          +----> MISP (recommended IOC source of truth)
          |        |
          |        +----> OpenCTI (optional graph/campaign context)
          |
          +----> Public projection index
                       |
                       +----> this portal / REST API / TAXII gateway
```

The public portal should never query an unrestricted analyst store directly.
Publish only reviewed, policy-approved fields into a separate projection.

## Production adapter contract

Replace the in-browser seed lookup in `dist/core.js` with an HTTPS endpoint:

```http
POST /v1/indicators/check
Content-Type: application/json

{"type":"bank-account","value":"0123456789","bank_code":"ACB"}
```

The response should preserve the fields currently used by the UI:
`riskScore`, `confidence`, `status`, `reportCount`, `firstSeen`, `lastSeen`,
`scamTypes`, `summary`, and policy-safe `sources`.

## Current MVP limitations

- Lookup and submitted reports run in the browser.
- Submitted reports are stored only in `localStorage` on the current device.
- There is no authentication, analyst workflow, server database, or live MISP/OpenCTI connection yet.
- Search is exact-match after normalization, intentionally preventing bulk enumeration.

## Next milestone

1. Add an ingestion API and PostgreSQL review queue.
2. Add a MISP publisher/consumer adapter.
3. Add analyst login and evidence upload.
4. Add tenant-scoped API keys and audit logs.
5. Expose approved partner feeds via REST and TAXII 2.1.
