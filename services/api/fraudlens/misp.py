from __future__ import annotations

import httpx

from .config import Settings


class MispClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def publishable_attributes(self) -> list[dict]:
        if not self.settings.misp_configured:
            raise RuntimeError("MISP_URL and MISP_API_KEY must be configured")

        headers = {
            "Authorization": self.settings.misp_api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "returnFormat": "json",
            "type": ["bank-account-nr", "iban", "phone-number", "url", "domain"],
            "tags": self.settings.misp_publish_tag,
            "includeContext": True,
            "includeEventTags": True,
            "limit": 5000,
        }
        async with httpx.AsyncClient(
            base_url=self.settings.misp_url.rstrip("/"),
            verify=self.settings.misp_verify_tls,
            timeout=30,
        ) as client:
            response = await client.post("/attributes/restSearch", headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()
        if isinstance(body, list):
            return body
        return list((body.get("response") or {}).get("Attribute") or body.get("Attribute") or [])
