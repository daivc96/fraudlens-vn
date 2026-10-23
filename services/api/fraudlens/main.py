from __future__ import annotations

import secrets

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .core import from_misp_attribute
from .misp import MispClient
from .models import LookupRequest, ReportRequest
from .seed import DEMO_INDICATORS
from .store import Store


app = FastAPI(
    title="FraudLens Projection API",
    version="0.2.0",
    description="Public-safe exact-match projection in front of MISP.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Sync-Token"],
)
store = Store(settings.db_path)


def require_sync_token(x_sync_token: str = Header(default="")) -> None:
    if not settings.sync_token or not secrets.compare_digest(x_sync_token, settings.sync_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid sync token")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": app.version,
        "misp_configured": settings.misp_configured,
        **store.counts(),
    }


@app.post("/v1/indicators/check")
def lookup(request: LookupRequest) -> dict:
    record = store.lookup(request.type, request.value)
    if record is None:
        return {"matched": False, "notice": "No exact match. This does not mean the indicator is safe."}
    return {"matched": True, "indicator": record}


@app.post("/v1/reports", status_code=status.HTTP_202_ACCEPTED)
def submit_report(request: ReportRequest) -> dict:
    report_id = store.add_report(request.model_dump(mode="json"))
    return {"accepted": True, "report_id": report_id, "status": "pending"}


@app.post("/internal/seed-demo", dependencies=[Depends(require_sync_token)])
def seed_demo() -> dict:
    for indicator in DEMO_INDICATORS:
        store.upsert(indicator)
    return {"seeded": len(DEMO_INDICATORS), **store.counts()}


@app.post("/internal/sync/misp", dependencies=[Depends(require_sync_token)])
async def sync_misp() -> dict:
    try:
        attributes = await MispClient(settings).publishable_attributes()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except httpx.HTTPError as error:
        raise HTTPException(status_code=502, detail=f"MISP request failed: {error}") from error

    imported = 0
    skipped = 0
    for attribute in attributes:
        projection = from_misp_attribute(attribute)
        if projection is None:
            skipped += 1
            continue
        store.upsert(projection)
        imported += 1
    return {"received": len(attributes), "imported": imported, "skipped": skipped, **store.counts()}
