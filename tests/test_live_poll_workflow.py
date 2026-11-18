from __future__ import annotations

from poll_session_models import LivePollSessionBundle, VotePublishRequest, VoteTally
from poll_session_service import PollSessionService


class FakeGateway:
    def __init__(self) -> None:
        self.published: list[dict[str, str]] = []

    def create_realtime_channel(self, channel: str) -> None:
        return None

    def issue_viewer_token(self, client_id: str, channel: str) -> str:
        return "viewer-token"

    def create_creator_room(self, room: str, region: str) -> None:
        return None

    def issue_creator_token(self, room: str, identity: str, display_name: str) -> str:
        return "creator-token"

    def publish_creator_update(self, channel: str, event: str, data: str, account_id: str) -> None:
        self.published.append(
            {
                "channel": channel,
                "event": event,
                "data": data,
                "account_id": account_id,
            }
        )


def test_vote_update_moves_session_live_and_publishes_creator_event() -> None:
    gateway = FakeGateway()
    service = PollSessionService(gateway)
    session = LivePollSessionBundle(
        session_id="sess_123",
        ingest_channel="poll.stream_42.poll_finale.audience",
        creator_channel="poll.stream_42.poll_finale.creator",
        creator_room="creator-stream_42-poll_finale",
        viewer_token="viewer-token",
        creator_token="creator-token",
        status="ready",
    )

    update = service.publish_vote_update(
        session,
        VotePublishRequest(
            tallies=[
                VoteTally(option_id="opt_a", votes=0),
                VoteTally(option_id="opt_b", votes=3),
            ]
        ),
    )

    assert update.status == "live"
    assert update.leading_option_id == "opt_b"
    assert update.total_votes == 3
    assert len(gateway.published) == 1
    assert gateway.published[0]["channel"] == "poll.stream_42.poll_finale.creator"
    assert gateway.published[0]["event"] == "poll.vote_update"
