import time
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

METRICS = """
# HELP openclaw_strategy_evaluated_total Strategies evaluated
# TYPE openclaw_strategy_evaluated_total counter
openclaw_strategy_evaluated_total 0
# HELP openclaw_strategy_accepted_total Strategies accepted
# TYPE openclaw_strategy_accepted_total counter
openclaw_strategy_accepted_total 0
# HELP openclaw_worker_queue_depth Worker queue depth
# TYPE openclaw_worker_queue_depth gauge
openclaw_worker_queue_depth 0
"""

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(404); self.end_headers(); return
        self.send_response(200)
        self.send_header('Content-Type','text/plain; version=0.0.4')
        self.end_headers()
        self.wfile.write(METRICS.encode())
    def log_message(self, fmt, *args):
        return

if __name__ == '__main__':
    port = 8200
    print(json.dumps({"ts": int(time.time()), "event": "strategy_stub_started", "port": port}))
    HTTPServer(('127.0.0.1', port), H).serve_forever()
