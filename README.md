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

## Local MISP + projection API

The next-stage local stack is now included:

```bash
make configure
make misp-bootstrap
make misp-up
make api-up
```

- MISP analyst UI: `https://localhost:10443`
- FraudLens API: `http://localhost:8080`
- API documentation: `http://localhost:8080/docs`
- Portal connected to the local API: `http://localhost:4173/?api=http://localhost:8080`

MISP remains localhost-only. FraudLens imports only attributes tagged
`fraudlens:publish=true` into a separate SQLite public projection. See
[`docs/MISP-INTEGRATION.md`](docs/MISP-INTEGRATION.md) for setup, tag conventions,
sync, and lookup examples.

## Test

```bash
npm test
npm run check
python3 -m unittest discover -s services/api/tests
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

The browser uses demo data by default. Add `?api=https://your-api.example` to
connect it to a deployed projection API. The current endpoint contract is:

```http
POST /v1/indicators/check
Content-Type: application/json

{"type":"bank-account","value":"0123456789","bank_code":"ACB"}
```

The response should preserve the fields currently used by the UI:
`riskScore`, `confidence`, `status`, `reportCount`, `firstSeen`, `lastSeen`,
`scamTypes`, `summary`, and policy-safe `sources`.

## Current limitations

- The hosted demo still uses browser seed data until the API is deployed publicly.
- The local API has a SQLite projection and MISP sync, but no analyst SSO yet.
- Submitted reports in the hosted demo still use `localStorage`; the local API exposes a durable pending-report endpoint.
- Search is exact-match after normalization, intentionally preventing bulk enumeration.

## Next milestone

1. Add an ingestion API and PostgreSQL review queue.
2. Add a MISP publisher/consumer adapter.
3. Add analyst login and evidence upload.
4. Add tenant-scoped API keys and audit logs.
5. Expose approved partner feeds via REST and TAXII 2.1.
