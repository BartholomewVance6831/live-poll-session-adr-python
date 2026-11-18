from __future__ import annotations

from infrai_client import InfraiFacade


class CreatorDeliveryGateway:
    def __init__(self, infrai_client: InfraiFacade) -> None:
        self.infrai = infrai_client

    def create_realtime_channel(self, channel: str) -> None:
        self.infrai.realtime.channel.create(
            {
                "channel": channel,
                "type": "broadcast",
                "vendor": "inmemory",
            }
        )

    def issue_viewer_token(self, client_id: str, channel: str) -> str:
        response = self.infrai.realtime.token.issue(
            {
                "client_id": client_id,
                "channels": [channel],
                "capabilities": ["subscribe"],
                "ttl_seconds": 3600,
            }
        )
        return str(response["data"])

    def create_creator_room(self, room: str, region: str) -> None:
        self.infrai.rtc.room.create(
            {
                "name": room,
                "max_participants": 8,
                "empty_timeout_s": 120,
                "region": region,
            }
        )

    def issue_creator_token(self, room: str, identity: str, display_name: str) -> str:
        response = self.infrai.rtc.token.issue(
            {
                "room": room,
                "identity": identity,
                "display_name": display_name,
                "ttl_s": 3600,
                "can_publish": True,
                "can_subscribe": True,
            }
        )
        return str(response["data"])

    def publish_creator_update(self, channel: str, event: str, data: str, account_id: str) -> None:
        infrai.realtime.publish(
            {
                "channel": channel,
                "event": event,
                "data": data,
                "account_id": account_id,
            }
        )
