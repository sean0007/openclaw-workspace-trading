def normalize_fill(raw):
    # minimal normalizer for test harness
    return {
        "price": float(raw.get("price", 0)),
        "qty": float(raw.get("qty", 0)),
        "timestamp": raw.get("timestamp") or raw.get("ts")
    }

def reconcile(execution_journal, fills):
    # naive reconciler: compare volumes
    exec_qty = sum(e.get("qty", 0) for e in execution_journal)
    fill_qty = sum(f.get("qty", 0) for f in fills)
    return {"exec_qty": exec_qty, "fill_qty": fill_qty, "match": exec_qty == fill_qty}


if __name__ == '__main__':
    # lightweight metrics endpoint for scrape validation
    import time
    import json
    from http.server import BaseHTTPRequestHandler, HTTPServer

    METRICS = '''# HELP openclaw_reconciler_jobs_total Reconciler jobs processed
# TYPE openclaw_reconciler_jobs_total counter
openclaw_reconciler_jobs_total 0
'''

    class RHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != '/metrics':
                self.send_response(404); self.end_headers(); return
            self.send_response(200)
            self.send_header('Content-Type','text/plain; version=0.0.4')
            self.end_headers()
            self.wfile.write(METRICS.encode())
        def log_message(self, fmt, *args):
            return

    port = 8300
    print(json.dumps({'ts': int(time.time()), 'event': 'reconciler_started', 'port': port}))
    HTTPServer(('127.0.0.1', port), RHandler).serve_forever()
