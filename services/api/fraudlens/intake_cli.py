from __future__ import annotations

import argparse
import asyncio
import json

import httpx

from .config import settings
from .intake import Intake, build_event_payload


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Create a reviewed Facebook intake event in MISP")
    result.add_argument("--type", required=True, choices=["bank-account", "phone-number", "url"])
    result.add_argument("--value", required=True)
    result.add_argument("--source-url", required=True)
    result.add_argument("--scenario", required=True)
    result.add_argument("--reviewed-by", required=True)
    result.add_argument("--bank-code", default="")
    result.add_argument("--risk", type=int, default=45)
    result.add_argument("--confidence", choices=["low", "medium", "high"], default="low")
    result.add_argument("--source-count", type=int, default=1)
    result.add_argument("--approve-public", action="store_true")
    result.add_argument("--single-source-exception", action="store_true")
    return result


async def run() -> None:
    args = parser().parse_args()
    if not settings.misp_configured:
        raise SystemExit("MISP_URL and MISP_API_KEY are not configured")
    intake = Intake(
        indicator_type=args.type,
        value=args.value,
        source_url=args.source_url,
        scenario=args.scenario,
        reviewed_by=args.reviewed_by,
        bank_code=args.bank_code,
        risk_score=args.risk,
        confidence=args.confidence,
        source_count=args.source_count,
        approve_public=args.approve_public,
        single_source_exception=args.single_source_exception,
    )
    headers = {
        "Authorization": settings.misp_api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(
        base_url=settings.misp_url.rstrip("/"),
        verify=settings.misp_verify_tls,
        timeout=30,
    ) as client:
        response = await client.post("/events/add", headers=headers, json=build_event_payload(intake))
        response.raise_for_status()
        body = response.json()
    event = body.get("Event") or body
    print(json.dumps({"created": True, "event_id": event.get("id"), "published_to_projection": args.approve_public}))


if __name__ == "__main__":
    asyncio.run(run())
