import threading
import json
import urllib.request
import time

from execution_service import ExecutionService
from secrets_manager import get_secrets_manager


def test_production_readiness_basic(tmp_path):
    # Start execution service with file-backed secrets manager
    secrets_path = tmp_path / "secrets.json"
    mgr = get_secrets_manager(str(secrets_path))
    # ensure execution HMAC key exists
    if hasattr(mgr, "set_secret"):
        mgr.set_secret("exec_hmac_key", "testkey")

    srv = ExecutionService(("127.0.0.1", 0), db_path=str(tmp_path / "exec.db"), secrets_manager=mgr, operator_api_key="opkey")
    host, port = srv.server_address
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()

    try:
        # metrics endpoint should be reachable
        with urllib.request.urlopen(f"http://{host}:{port}/metrics", timeout=2) as resp:
            txt = resp.read().decode()
        assert "openclaw_execute_requests_total" in txt

        # state endpoint should show default boot_completed as False
        with urllib.request.urlopen(f"http://{host}:{port}/state", timeout=2) as resp:
            state = json.loads(resp.read())
        assert state.get("boot_completed") in (False, 0)

        # perform boot complete via operator key header
        req = urllib.request.Request(f"http://{host}:{port}/boot/complete", data=json.dumps({"actor": "test"}).encode(), headers={"Content-Type": "application/json", "X-OP-API-KEY": "opkey"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            res = json.loads(resp.read())
        assert res.get("boot_completed") is True

        # state should now reflect boot completed
        with urllib.request.urlopen(f"http://{host}:{port}/state", timeout=2) as resp:
            state2 = json.loads(resp.read())
        assert state2.get("boot_completed") is True

    finally:
        srv.shutdown()
        thread.join(timeout=2)
