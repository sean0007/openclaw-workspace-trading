import os
import hmac
import hashlib
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from secrets_manager import get_secrets_manager

KEY_NAME = "signer_hmac_key"
API_KEY_ENV = "SIGNER_API_KEY"


class SignHandler(BaseHTTPRequestHandler):
    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        try:
            if self.path != "/sign":
                return self._respond(404, {"error": "not_found"})
            apikey = self.headers.get("X-API-KEY")
            if not apikey or apikey != self.server.api_key:
                return self._respond(403, {"error": "forbidden"})
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw)
            except Exception:
                return self._respond(400, {"error": "bad_json"})
            order_id = payload.get("order_id")
            strategy_id = payload.get("strategy_id")
            if not order_id or not strategy_id:
                return self._respond(400, {"error": "missing_fields"})

            timestamp = int(time.time())
            nonce = os.urandom(16).hex()
            expiry = timestamp + 5
            msg = f"{order_id}|{timestamp}|{nonce}|{expiry}|{strategy_id}".encode()
            key_bytes = self.server.signing_key
            sig = hmac.new(key_bytes, msg, hashlib.sha256).hexdigest()
            token = {"order_id": order_id, "timestamp": timestamp, "nonce": nonce, "expiry": expiry, "strategy_id": strategy_id, "sig": sig}
            try:
                audit_path = os.getenv("SIGNER_AUDIT_LOG", "/tmp/signer_audit.log")
                with open(audit_path, "a") as f:
                    f.write(json.dumps({"ts": timestamp, "event": "token_issued", "strategy_id": strategy_id, "order_id": order_id}) + "\n")
            except Exception as exc:
                print(json.dumps({"ts": int(time.time()), "event": "signer_audit_write_failed", "reason": str(exc)}))
            # increment issued token metric
            try:
                self.server._metrics["tokens_issued_total"] += 1
            except Exception:
                pass
            return self._respond(200, {"token": token})
        except Exception as exc:
            print(json.dumps({"ts": int(time.time()), "event": "signer_error", "reason": str(exc)}))
            return self._respond(500, {"error": "internal_error"})

    def log_message(self, format, *args):
        return

    def do_GET(self):
        # Expose minimal Prometheus-style metrics for monitoring/scraping
        if self.path == "/metrics":
            val = 0
            try:
                val = int(self.server._metrics.get("tokens_issued_total", 0))
            except Exception:
                val = 0
            metrics = (
                "# HELP openclaw_signer_tokens_issued_total Tokens issued by signer\n"
                "# TYPE openclaw_signer_tokens_issued_total counter\n"
                f"openclaw_signer_tokens_issued_total {val}\n"
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            self.wfile.write(metrics.encode())
            return
        return self._respond(404, {"error": "not_found"})


class SignerService(HTTPServer):
    def __init__(self, addr, secrets_manager, api_key, **kwargs):
        super().__init__(addr, SignHandler)
        self.secrets_manager = secrets_manager
        self.signing_key = self.secrets_manager.get_secret(KEY_NAME)
        self.api_key = api_key
        # simple in-memory metrics
        self._metrics = {
            "tokens_issued_total": 0,
        }


def run_service(host="127.0.0.1", port=9000, secrets_path=None, key_path=None, api_key="test-api-key"):
    secrets_manager = get_secrets_manager(secrets_path)
    if key_path and hasattr(secrets_manager, "set_secret"):
        with open(key_path, "rb") as f:
            secrets_manager.set_secret(KEY_NAME, f.read().strip().decode())
    srv = SignerService((host, port), secrets_manager, api_key)
    print(json.dumps({"ts": int(time.time()), "event": "signer_started", "host": host, "port": port}))
    try:
        srv.serve_forever()
    finally:
        srv.server_close()


if __name__ == "__main__":
    run_service()
