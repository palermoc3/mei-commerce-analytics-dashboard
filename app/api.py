from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from starlette.types import Receive, Scope, Send

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "public" / "kpis.json"


def load_payload(path: Path = DEFAULT_JSON) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] != "http":
        await send({"type": "http.response.start", "status": 404, "headers": []})
        await send({"type": "http.response.body", "body": b""})
        return

    path = scope["path"]
    if path in {"/", "/healthz"}:
        payload = {"status": "ok"}
        status = 200
    elif path == "/api/kpis":
        payload = load_payload(DEFAULT_JSON)
        status = 200
    else:
        payload = {"error": "not found"}
        status = 404

    body = json.dumps(payload).encode("utf-8")
    headers = [
        (b"content-type", b"application/json; charset=utf-8"),
        (b"content-length", str(len(body)).encode("ascii")),
    ]

    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


def create_app() -> Any:
    return app


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
