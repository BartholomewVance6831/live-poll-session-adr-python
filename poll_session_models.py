from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PollOption(BaseModel):
    option_id: str
    label: str


class LivePollSessionRequest(BaseModel):
    stream_id: str
    creator_id: str
    poll_id: str
    question: str
    options: list[PollOption] = Field(min_length=2)
    region: str = "us-east"


class VoteTally(BaseModel):
    option_id: str
    votes: int = Field(ge=0)


class VotePublishRequest(BaseModel):
    tallies: list[VoteTally] = Field(min_length=1)


class LivePollSessionBundle(BaseModel):
    session_id: str
    ingest_channel: str
    creator_channel: str
    creator_room: str
    viewer_token: str
    creator_token: str
    status: Literal["ready", "live"]


class CreatorDeliveryUpdate(BaseModel):
    session_id: str
    status: Literal["ready", "live"]
    leading_option_id: str
    total_votes: int
