from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, model_validator


IndicatorType = Literal["bank-account", "phone-number", "url"]


class LookupRequest(BaseModel):
    type: IndicatorType
    value: str = Field(min_length=5, max_length=2048)
    bank_code: str | None = Field(default=None, max_length=30)


class ReportRequest(BaseModel):
    type: IndicatorType
    value: str = Field(min_length=5, max_length=2048)
    source_url: HttpUrl | None = None
    description: str = Field(min_length=20, max_length=5000)
    has_evidence: bool = False

    @model_validator(mode="after")
    def require_evidence_context(self):
        if self.source_url is None and not self.has_evidence:
            raise ValueError("source_url or has_evidence is required")
        return self
