from __future__ import annotations

from dataclasses import dataclass
from datetime import date


MISP_TYPES = {
    "bank-account": ("bank-account-nr", "Financial fraud"),
    "phone-number": ("phone-number", "Network activity"),
    "url": ("url", "Network activity"),
}


@dataclass(frozen=True)
class Intake:
    indicator_type: str
    value: str
    source_url: str
    scenario: str
    reviewed_by: str
    bank_code: str = ""
    risk_score: int = 45
    confidence: str = "low"
    source_count: int = 1
    approve_public: bool = False
    single_source_exception: bool = False

    def validate(self) -> None:
        if self.indicator_type not in MISP_TYPES:
            raise ValueError(f"Unsupported indicator type: {self.indicator_type}")
        if not self.value.strip() or not self.source_url.startswith("https://"):
            raise ValueError("A value and an HTTPS source URL are required")
        if not self.reviewed_by.strip() or len(self.scenario.strip()) < 20:
            raise ValueError("reviewed_by and a scenario of at least 20 characters are required")
        if not 0 <= self.risk_score <= 100:
            raise ValueError("risk_score must be between 0 and 100")
        if self.approve_public and self.source_count < 2 and not self.single_source_exception:
            raise ValueError("Public approval needs two sources or --single-source-exception")


def build_event_payload(intake: Intake) -> dict:
    intake.validate()
    misp_type, category = MISP_TYPES[intake.indicator_type]
    tags = [
        "fraudlens:status=community-reported",
        f"fraudlens:risk={intake.risk_score}",
        f"fraudlens:confidence={intake.confidence}",
        f"fraudlens:sources={intake.source_count}",
        f"fraudlens:scam-type={intake.scenario}",
        "fraudlens:source=facebook",
    ]
    if intake.approve_public:
        tags.append("fraudlens:publish=true")

    comment = (
        "Community report collected from a public Facebook post; allegation not independently "
        f"adjudicated. Review: {intake.reviewed_by}."
    )
    if intake.bank_code:
        comment += f" Bank code reported: {intake.bank_code.upper()}."

    return {
        "Event": {
            "info": f"FraudLens intake: {intake.scenario} ({date.today().isoformat()})",
            "distribution": "0",
            "threat_level_id": "3",
            "analysis": "1",
            "published": False,
            "Tag": [{"name": tag} for tag in tags],
            "Attribute": [
                {
                    "type": misp_type,
                    "category": category,
                    "to_ids": False,
                    "value": intake.value,
                    "comment": comment,
                    "Tag": [{"name": tag} for tag in tags],
                },
                {
                    "type": "link",
                    "category": "External analysis",
                    "to_ids": False,
                    "value": intake.source_url,
                    "comment": "Public source retained for analyst verification.",
                },
            ],
        }
    }
