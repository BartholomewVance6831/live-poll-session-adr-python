from __future__ import annotations

import json

from creator_delivery_gateway import CreatorDeliveryGateway
from infrai_client import infrai
from poll_session_models import LivePollSessionRequest, PollOption, VotePublishRequest, VoteTally
from poll_session_service import PollSessionService


def main() -> None:
    service = PollSessionService(CreatorDeliveryGateway(infrai))

    session = service.open_session(
        LivePollSessionRequest(
            stream_id="stream_42",
            creator_id="creator_9",
            poll_id="poll_finale",
            question="Which ending should air?",
            options=[
                PollOption(option_id="ending_a", label="Ending A"),
                PollOption(option_id="ending_b", label="Ending B"),
            ],
            region="us-east",
        )
    )

    update = service.publish_vote_update(
        session,
        VotePublishRequest(
            tallies=[
                VoteTally(option_id="ending_a", votes=12),
                VoteTally(option_id="ending_b", votes=18),
            ]
        ),
    )

    print(json.dumps({"session": session.model_dump(), "update": update.model_dump()}, indent=2))


if __name__ == "__main__":
    main()
