import os
import threading
import time
import json
import urllib.request

from execution_service import ExecutionService
from secrets_manager import FileSecretsManager
from risk_engine import RiskEngine


def test_risk_engine_notifies_execution_gateway(tmp_path):
    # prepare secrets file for execution service
    secrets_path = tmp_path / "secrets.json"
    secrets_mgr = FileSecretsManager(str(secrets_path))
    # set execution key (not used in this test but execution service expects it)
    secrets_mgr.set_secret("exec_hmac_key", "dummykey")

    # start execution service on ephemeral port
    srv = ExecutionService(("127.0.0.1", 0), db_path=str(tmp_path / "exec.db"), secrets_manager=secrets_mgr, operator_api_key="opkey")
    host, port = srv.server_address
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()

    try:
        # configure risk engine to point at the running execution service
        os.environ["RISK_CIRCUIT_SHARED_SECRET"] = "risk-secret"
        os.environ["EXEC_GATEWAY_RISK_URL"] = f"http://{host}:{port}/risk/lock"
        os.environ["SIGNER_API_KEY"] = "dummy-signer"

        re = RiskEngine(execution_engine=None, wallet_balance_provider=lambda: 100000.0)

        # trigger local kill which should also POST to the execution gateway
        re._activate_kill("unit_test_trigger")

        # query gateway state
        with urllib.request.urlopen(f"http://{host}:{port}/state", timeout=2) as resp:
            body = json.loads(resp.read())
        assert body.get("risk_locked") is True

    finally:
        srv.shutdown()
        thread.join(timeout=2)
