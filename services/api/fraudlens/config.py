from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("FRAUDLENS_DB_PATH", "/data/fraudlens.db")
    sync_token: str = os.getenv("FRAUDLENS_SYNC_TOKEN", "")
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv(
            "FRAUDLENS_ALLOWED_ORIGINS", "http://localhost:4173"
        ).split(",")
        if origin.strip()
    )
    misp_url: str = os.getenv("MISP_URL", "")
    misp_api_key: str = os.getenv("MISP_API_KEY", "")
    misp_verify_tls: bool = _as_bool(os.getenv("MISP_VERIFY_TLS"), True)
    misp_publish_tag: str = os.getenv(
        "MISP_PUBLISH_TAG", "fraudlens:publish=true"
    )

    @property
    def misp_configured(self) -> bool:
        return bool(
            self.misp_url
            and self.misp_api_key
            and not self.misp_api_key.startswith("replace-")
        )


settings = Settings()
