from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit


TYPE_MAP = {
    "bank-account-nr": "bank-account",
    "iban": "bank-account",
    "phone-number": "phone-number",
    "url": "url",
    "domain": "url",
}


def normalize_value(indicator_type: str, raw_value: str) -> str:
    value = str(raw_value or "").strip()
    if indicator_type == "bank-account":
        return "".join(character for character in value.upper() if character.isalnum())
    if indicator_type == "phone-number":
        digits = "".join(character for character in value if character.isdigit())
        return f"0{digits[2:]}" if digits.startswith("84") and len(digits) >= 11 else digits
    if indicator_type == "url":
        candidate = value if "://" in value else f"https://{value}"
        parsed = urlsplit(candidate)
        host = (parsed.hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        path = parsed.path.rstrip("/")
        return f"{host}{path}" if host else value.lower().rstrip("/")
    return value


def mask_value(indicator_type: str, normalized_value: str) -> str:
    if indicator_type == "bank-account" and len(normalized_value) >= 7:
        return f"{normalized_value[:4]} **** {normalized_value[-2:]}"
    if indicator_type == "phone-number" and len(normalized_value) >= 8:
        return f"{normalized_value[:4]} *** {normalized_value[-3:]}"
    if indicator_type == "url":
        return normalized_value.replace(".", "[.]", 1)
    return "***"


def tag_value(tags: list[str], prefix: str, default: str = "") -> str:
    for tag in tags:
        if tag.startswith(prefix):
            return tag[len(prefix) :]
    return default


def parse_risk(tags: list[str], default: int = 50) -> int:
    raw = tag_value(tags, "fraudlens:risk=", str(default))
    try:
        return max(0, min(100, int(raw)))
    except ValueError:
        return default


@dataclass(frozen=True)
class ProjectionIndicator:
    indicator_type: str
    normalized_value: str
    display_value: str
    risk_score: int
    confidence: str
    status: str
    report_count: int
    independent_sources: int
    first_seen: str
    last_seen: str
    scam_types: list[str]
    summary: str
    source_ref: str


def from_misp_attribute(attribute: dict) -> ProjectionIndicator | None:
    indicator_type = TYPE_MAP.get(str(attribute.get("type", "")))
    if not indicator_type:
        return None
    normalized = normalize_value(indicator_type, str(attribute.get("value", "")))
    if not normalized:
        return None

    tag_objects = attribute.get("Tag", []) or []
    event_tags = (attribute.get("Event", {}) or {}).get("Tag", []) or []
    tags = [str(tag.get("name", "")) for tag in [*tag_objects, *event_tags]]
    scam_types = [tag.split("=", 1)[1] for tag in tags if tag.startswith("fraudlens:scam-type=")]
    event = attribute.get("Event", {}) or {}
    return ProjectionIndicator(
        indicator_type=indicator_type,
        normalized_value=normalized,
        display_value=mask_value(indicator_type, normalized),
        risk_score=parse_risk(tags),
        confidence=tag_value(tags, "fraudlens:confidence=", "medium"),
        status=tag_value(tags, "fraudlens:status=", "reported"),
        report_count=max(1, int(attribute.get("sighting_count") or 1)),
        independent_sources=max(1, int(tag_value(tags, "fraudlens:sources=", "1"))),
        first_seen=str(attribute.get("first_seen") or attribute.get("date") or event.get("date") or ""),
        last_seen=str(attribute.get("last_seen") or attribute.get("date") or event.get("date") or ""),
        scam_types=scam_types or ["Chưa phân loại"],
        summary=str(attribute.get("comment") or "Chỉ báo được đồng bộ từ MISP sau khi qua policy publish."),
        source_ref=f"misp-attribute:{attribute.get('uuid') or attribute.get('id') or 'unknown'}",
    )
