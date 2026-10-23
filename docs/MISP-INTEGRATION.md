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

## Facebook intake

Search Facebook manually from an analyst account and retain the exact public
post URL, the reported indicator, scenario, post date, and screenshots. A
single post is an allegation, not proof. Intake therefore defaults to an
unpublished MISP event.

```bash
docker compose exec -T fraudlens-api python -m fraudlens.intake_cli \
  --type bank-account \
  --value '<reported-account>' \
  --bank-code '<bank-code>' \
  --source-url 'https://www.facebook.com/...' \
  --scenario 'Mua bán online nhận tiền rồi ngắt liên lạc' \
  --reviewed-by 'analyst@company.example'
```

After review, add `--approve-public`. Two independent sources are required by
default. For an explicitly accepted single-source warning, also pass
`--single-source-exception`; the record stays `community-reported` with low
confidence. Then run `make sync` to update the exact-match public projection.

Never put the account holder's name or screenshots into the public response.
The MISP event keeps the source for analyst review, while lookup returns only a
masked value and policy-safe summary.

## Lookup example

```bash
curl -s http://localhost:8080/v1/indicators/check \
  -H 'Content-Type: application/json' \
  -d '{"type":"bank-account","value":"0123456789","bank_code":"ACB"}'
```

The API returns a masked value and explanatory metadata. There is deliberately
no endpoint for enumerating the full indicator dataset.
