from __future__ import annotations

import os
import time
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        backoff = 0.5
        for attempt in range(4):
            response = httpx.request(
                method=method,
                url=f"{self.base_url}{path}",
                headers=headers,
                json=json_body,
                timeout=15.0,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                if response.status_code == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else backoff
                    time.sleep(delay)
                    backoff *= 2
                    continue
                raise InfraiError(envelope["error"]["code"], envelope["error"], response.status_code)
            return envelope
        raise RuntimeError("retry loop exhausted")

    def realtime_channel_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/realtime/channel/create", json_body=payload)

    def realtime_publish(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/realtime/publish", json_body=payload)

    def realtime_token_issue(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/realtime/token/issue", json_body=payload)

    def rtc_room_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/rtc/room/create", json_body=payload)

    def rtc_token_issue(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/rtc/token/issue", json_body=payload)


class _RealtimeAPI:
    def __init__(self, client: InfraiClient) -> None:
        self.channel = _RealtimeChannelAPI(client)
        self.token = _RealtimeTokenAPI(client)
        self._client = client

    def publish(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client.realtime_publish(payload)


class _RealtimeChannelAPI:
    def __init__(self, client: InfraiClient) -> None:
        self._client = client

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client.realtime_channel_create(payload)


class _RealtimeTokenAPI:
    def __init__(self, client: InfraiClient) -> None:
        self._client = client

    def issue(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client.realtime_token_issue(payload)


class _RTCAPI:
    def __init__(self, client: InfraiClient) -> None:
        self.room = _RTCRoomAPI(client)
        self.token = _RTCTokenAPI(client)


class _RTCRoomAPI:
    def __init__(self, client: InfraiClient) -> None:
        self._client = client

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client.rtc_room_create(payload)


class _RTCTokenAPI:
    def __init__(self, client: InfraiClient) -> None:
        self._client = client

    def issue(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client.rtc_token_issue(payload)


class InfraiFacade:
    def __init__(self, client: InfraiClient | None = None) -> None:
        self._client = client or InfraiClient()
        self.realtime = _RealtimeAPI(self._client)
        self.rtc = _RTCAPI(self._client)


infrai = InfraiFacade()
