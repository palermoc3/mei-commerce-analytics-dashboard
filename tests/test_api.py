import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api import app


class DummySend:
    def __init__(self) -> None:
        self.messages = []

    async def __call__(self, message):
        self.messages.append(message)


async def receive() -> dict[str, object]:
    return {"type": "http.request", "body": b"", "more_body": False}


def test_kpis_endpoint_returns_payload() -> None:
    async def run() -> None:
        send = DummySend()
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/healthz",
            "headers": [],
            "query_string": b"",
            "client": ("127.0.0.1", 1234),
            "server": ("127.0.0.1", 8000),
            "scheme": "http",
            "http_version": "1.1",
        }
        await app(scope, receive, send)
        assert send.messages[0]["status"] == 200
        assert json.loads(send.messages[1]["body"].decode("utf-8")) == {"status": "ok"}

        send = DummySend()
        scope = {**scope, "path": "/api/kpis"}
        await app(scope, receive, send)
        payload = json.loads(send.messages[1]["body"].decode("utf-8"))
        assert send.messages[0]["status"] == 200
        assert payload["receita"]["revenue"] == 160692.02
        assert payload["operacao"]["completed_orders"] == 2127

    asyncio.run(run())
