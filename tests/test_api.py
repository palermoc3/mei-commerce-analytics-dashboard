import json
import sys
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api import create_app


def test_kpis_endpoint_returns_payload():
    server = create_app(host="127.0.0.1", port=8765)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        with urlopen("http://127.0.0.1:8765/healthz") as response:
            body = json.loads(response.read().decode("utf-8"))
            assert response.status == 200
            assert body == {"status": "ok"}

        with urlopen("http://127.0.0.1:8765/api/kpis") as response:
            body = json.loads(response.read().decode("utf-8"))
            assert response.status == 200
            assert body["receita"]["revenue"] == 160692.02
            assert body["operacao"]["completed_orders"] == 2127
    finally:
        server.shutdown()
        thread.join(timeout=2)
