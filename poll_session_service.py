from __future__ import annotations

from typing import Protocol

from poll_session_models import CreatorDeliveryUpdate, LivePollSessionBundle, LivePollSessionRequest, VotePublishRequest


class RealtimeAndRtcGateway(Protocol):
    def create_realtime_channel(self, channel: str) -> None: ...
    def issue_viewer_token(self, client_id: str, channel: str) -> str: ...
    def create_creator_room(self, room: str, region: str) -> None: ...
    def issue_creator_token(self, room: str, identity: str, display_name: str) -> str: ...
    def publish_creator_update(self, channel: str, event: str, data: str, account_id: str) -> None: ...


class PollSessionService:
    def __init__(self, gateway: RealtimeAndRtcGateway) -> None:
        self.gateway = gateway

    def open_session(self, request: LivePollSessionRequest) -> LivePollSessionBundle:
        session_id = f"sess_{request.stream_id}_{request.poll_id}"
        ingest_channel = f"poll.{request.stream_id}.{request.poll_id}.audience"
        creator_channel = f"poll.{request.stream_id}.{request.poll_id}.creator"
        creator_room = f"creator-{request.stream_id}-{request.poll_id}"

        self.gateway.create_realtime_channel(ingest_channel)
        self.gateway.create_realtime_channel(creator_channel)
        self.gateway.create_creator_room(creator_room, request.region)

        viewer_token = self.gateway.issue_viewer_token(
            client_id=f"viewer-{request.stream_id}",
            channel=ingest_channel,
        )
        creator_token = self.gateway.issue_creator_token(
            room=creator_room,
            identity=request.creator_id,
            display_name="Producer Console",
        )

        return LivePollSessionBundle(
            session_id=session_id,
            ingest_channel=ingest_channel,
            creator_channel=creator_channel,
            creator_room=creator_room,
            viewer_token=viewer_token,
            creator_token=creator_token,
            status="ready",
        )

    def publish_vote_update(self, session: LivePollSessionBundle, request: VotePublishRequest) -> CreatorDeliveryUpdate:
        total_votes = sum(item.votes for item in request.tallies)
        leading = max(request.tallies, key=lambda item: (item.votes, item.option_id))
        status = "live" if total_votes > 0 else "ready"

        update = CreatorDeliveryUpdate(
            session_id=session.session_id,
            status=status,
            leading_option_id=leading.option_id,
            total_votes=total_votes,
        )

        if total_votes > 0:
            self.gateway.publish_creator_update(
                channel=session.creator_channel,
                event="poll.vote_update",
                data=update.model_dump_json(),
                account_id=session.session_id,
            )

        return update
