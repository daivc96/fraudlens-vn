#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="${ROOT_DIR}/.runtime/misp-docker"
UPSTREAM_URL="https://github.com/MISP/misp-docker.git"

require_docker() {
  command -v docker >/dev/null 2>&1 || { echo "Docker is required." >&2; exit 1; }
  docker info >/dev/null 2>&1 || { echo "Docker daemon is not running. Start Docker Desktop first." >&2; exit 1; }
}

bootstrap() {
  require_docker
  if [[ ! -d "${RUNTIME_DIR}/.git" ]]; then
    mkdir -p "$(dirname "${RUNTIME_DIR}")"
    git clone --depth 1 "${UPSTREAM_URL}" "${RUNTIME_DIR}"
  fi

  if [[ ! -f "${RUNTIME_DIR}/.env" ]]; then
    cp "${RUNTIME_DIR}/template.env" "${RUNTIME_DIR}/.env"
    cat >> "${RUNTIME_DIR}/.env" <<'EOF'

# FraudLens local-only overrides. Do not expose these ports publicly.
BASE_URL=https://localhost:10443
NGINX_HTTP_PORT=127.0.0.1:10080
NGINX_HTTPS_PORT=127.0.0.1:10443
ADMIN_EMAIL=admin@fraudlens.local
ADMIN_ORG=FraudLens-Lab
TZ=Asia/Ho_Chi_Minh
DISABLE_PRINTING_PLAINTEXT_CREDENTIALS=true
EOF
  fi

  if [[ ! -f "${RUNTIME_DIR}/ssl/cert.pem" || ! -f "${RUNTIME_DIR}/ssl/key.pem" ]]; then
    mkdir -p "${RUNTIME_DIR}/ssl"
    openssl req -x509 -subj '/CN=localhost' -nodes -newkey rsa:4096 \
      -keyout "${RUNTIME_DIR}/ssl/key.pem" -out "${RUNTIME_DIR}/ssl/cert.pem" \
      -days 365 -addext 'subjectAltName = DNS:localhost, IP:127.0.0.1, IP:::1'
    chmod 600 "${RUNTIME_DIR}/ssl/key.pem"
    echo "Created a local self-signed TLS certificate."
  fi

  if grep -q '^ADMIN_KEY=$' "${RUNTIME_DIR}/.env"; then
    local admin_key admin_password
    admin_key="$(openssl rand -hex 20)"
    admin_password="$(openssl rand -hex 16)"
    sed -i.bak "s/^ADMIN_KEY=$/ADMIN_KEY=${admin_key}/" "${RUNTIME_DIR}/.env"
    sed -i.bak "s/^ADMIN_PASSWORD=$/ADMIN_PASSWORD=${admin_password}/" "${RUNTIME_DIR}/.env"
    rm -f "${RUNTIME_DIR}/.env.bak"
    printf 'MISP user: admin@fraudlens.local\nMISP password: %s\n' "${admin_password}" > "${ROOT_DIR}/.runtime/misp-credentials"
    chmod 600 "${ROOT_DIR}/.runtime/misp-credentials"
    if [[ -f "${ROOT_DIR}/.env" ]]; then
      sed -i.bak "s/^MISP_API_KEY=.*/MISP_API_KEY=${admin_key}/" "${ROOT_DIR}/.env"
      rm -f "${ROOT_DIR}/.env.bak"
    fi
    echo "Generated local credentials in .runtime/misp-credentials and wired the API key into .env."
  fi

  if [[ -f "${ROOT_DIR}/.env" ]] && grep -q '^FRAUDLENS_SYNC_TOKEN=replace-with-a-long-random-value$' "${ROOT_DIR}/.env"; then
    local sync_token
    sync_token="$(openssl rand -hex 32)"
    sed -i.bak "s/^FRAUDLENS_SYNC_TOKEN=replace-with-a-long-random-value$/FRAUDLENS_SYNC_TOKEN=${sync_token}/" "${ROOT_DIR}/.env"
    rm -f "${ROOT_DIR}/.env.bak"
    echo "Generated a local FraudLens sync token."
  fi
  echo "Official MISP Docker checkout ready at ${RUNTIME_DIR}"
}

case "${1:-}" in
  bootstrap)
    bootstrap
    ;;
  up)
    bootstrap
    docker compose --project-directory "${RUNTIME_DIR}" pull
    docker compose --project-directory "${RUNTIME_DIR}" up -d
    echo "MISP starting at https://localhost:10443"
    echo "Run: docker compose --project-directory ${RUNTIME_DIR} ps"
    ;;
  down)
    require_docker
    docker compose --project-directory "${RUNTIME_DIR}" down
    ;;
  logs)
    require_docker
    docker compose --project-directory "${RUNTIME_DIR}" logs -f misp-core misp-nginx
    ;;
  *)
    echo "Usage: $0 {bootstrap|up|down|logs}" >&2
    exit 2
    ;;
esac
