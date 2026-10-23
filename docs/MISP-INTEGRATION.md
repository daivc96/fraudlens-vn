# MISP integration

FraudLens uses MISP as the analyst-side source of truth and publishes only a
small, exact-match projection through its public API.

## Local topology

```text
MISP official Docker (https://localhost:10443)
        |
        | attributes/restSearch, API key, publish tag only
        v
FraudLens projection API (http://localhost:8080)
        |
        +-- SQLite public projection
        +-- exact-match lookup
        +-- pending community reports
```

MISP is bound to localhost and must not be exposed directly to the public
website. The projection API strips full values from responses and never offers
bulk listing.

## Start

Prerequisites: Docker Engine 25+ and Docker Compose 2.17+.

```bash
make configure
make misp-bootstrap
make misp-up
```

The bootstrap script downloads the official `MISP/misp-docker` repository into
the ignored `.runtime/` directory. MISP will start at
`https://localhost:10443`. It also creates a self-signed TLS certificate,
generates local credentials, and wires the MISP API key into the ignored root
`.env`. The MISP login is stored with mode `0600` in
`.runtime/misp-credentials`; never commit that file.

Then start FraudLens:

```bash
make api-up
make seed
```

Swagger UI is available at `http://localhost:8080/docs`.

## Publish policy

Only MISP attributes carrying this tag are imported:

```text
fraudlens:publish=true
```

Supported MISP types:

- `bank-account-nr` and `iban` → `bank-account`
- `phone-number` → `phone-number`
- `url` and `domain` → `url`

Optional policy tags:

```text
fraudlens:risk=82
fraudlens:status=suspected
fraudlens:confidence=high
fraudlens:sources=3
fraudlens:scam-type=Giả shipper
```

Run a policy-approved sync:

```bash
make sync
```

## Lookup example

```bash
curl -s http://localhost:8080/v1/indicators/check \
  -H 'Content-Type: application/json' \
  -d '{"type":"bank-account","value":"0123456789","bank_code":"ACB"}'
```

The API returns a masked value and explanatory metadata. There is deliberately
no endpoint for enumerating the full indicator dataset.
