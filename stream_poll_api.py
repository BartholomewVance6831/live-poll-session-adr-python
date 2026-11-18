from __future__ import annotations

from fastapi import FastAPI, HTTPException

from creator_delivery_gateway import CreatorDeliveryGateway
from infrai_client import InfraiError, infrai
from poll_session_models import LivePollSessionBundle, LivePollSessionRequest, VotePublishRequest
from poll_session_service import PollSessionService

api = FastAPI(title="stream-poll-session")
service = PollSessionService(CreatorDeliveryGateway(infrai))
_sessions: dict[str, LivePollSessionBundle] = {}


@api.post("/sessions", response_model=LivePollSessionBundle)
def create_session(request: LivePollSessionRequest) -> LivePollSessionBundle:
    try:
        session = service.open_session(request)
    except InfraiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    _sessions[session.session_id] = session
    return session


@api.post("/sessions/{session_id}/votes/publish")
def publish_votes(session_id: str, request: VotePublishRequest) -> dict[str, str | int]:
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail={"message": "session not found"})
    try:
        update = service.publish_vote_update(session, request)
    except InfraiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return update.model_dump()
