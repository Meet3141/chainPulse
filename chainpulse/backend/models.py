"""
ChainPulse — Pydantic Models for API request/response types.
"""
from pydantic import BaseModel, Field
from typing import Optional


class DisruptRequest(BaseModel):
    node: str = Field(..., description="Node ID to disrupt")
    severity: float = Field(..., ge=0.0, le=1.0)
    event_type: str = Field(..., description="Type of disruption event")


class RerouteRequest(BaseModel):
    shipment_ids: list[str] = Field(...)
    option_index: int = Field(..., ge=0, le=1)
    auto: bool = Field(default=False)
