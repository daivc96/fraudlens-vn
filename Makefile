.PHONY: help configure api-up api-down api-logs misp-bootstrap misp-up misp-down misp-logs sync seed test

-include .env
export

help:
	@echo "FraudLens local development"
	@echo "  make configure       Create local .env from the safe example"
	@echo "  make misp-bootstrap  Download the official MISP Docker project"
	@echo "  make misp-up         Start MISP on https://localhost:10443"
	@echo "  make api-up          Start the projection API on http://localhost:8080"
	@echo "  make seed            Load synthetic demo indicators into the projection"
	@echo "  make sync            Pull policy-approved attributes from MISP"
	@echo "  make test            Run JavaScript and Python unit tests"

configure:
	@test -f .env || cp .env.example .env
	@echo "Local .env is ready. MISP bootstrap will generate local-only credentials."

misp-bootstrap:
	@./scripts/misp-local.sh bootstrap

misp-up:
	@./scripts/misp-local.sh up

misp-down:
	@./scripts/misp-local.sh down

misp-logs:
	@./scripts/misp-local.sh logs

api-up: configure
	docker compose -f compose.local.yml up -d --build --wait

api-down:
	docker compose -f compose.local.yml down

api-logs:
	docker compose -f compose.local.yml logs -f fraudlens-api

seed:
	curl -fsS -X POST http://localhost:8080/internal/seed-demo -H "X-Sync-Token: $${FRAUDLENS_SYNC_TOKEN}" | python3 -m json.tool

sync:
	curl -fsS -X POST http://localhost:8080/internal/sync/misp -H "X-Sync-Token: $${FRAUDLENS_SYNC_TOKEN}" | python3 -m json.tool

test:
	npm test
	npm run check
	python3 -m unittest discover -s services/api/tests -v
