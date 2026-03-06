#!/usr/bin/env python3
"""Simple HTTP webhook receiver for Alertmanager alerts.

Writes incoming alerts as JSON lines to /tmp/alertmanager_received.jsonl and
prints a short log to stdout. Used for local testing of Alertmanager webhook
delivery.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# write alerts into mounted data dir so they persist in the repo when testing
OUTPATH = '/srv/data/alertmanager_received.jsonl'
# rotation: when OUTPATH exceeds ROTATE_MAX bytes, rotate and keep ROTATE_KEEP backups
ROTATE_MAX = 10 * 1024 * 1024  # 10 MB
ROTATE_KEEP = 10


class ReceiverHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        try:
            data = json.loads(body)
        except Exception:
            self.send_response(400)
            self.end_headers()
            return
        # ensure data directory exists, then append with a timestamp
        import os
        try:
            os.makedirs(os.path.dirname(OUTPATH), exist_ok=True)
        except Exception:
            pass
        entry = {'received_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z', 'payload': data}
        try:
            s = json.dumps(entry)
            with open(OUTPATH, 'a') as f:
                f.write(s + '\n')
        except Exception as exc:
            print('write failed', exc)
        # simple rotation
        try:
            import os
            if os.path.exists(OUTPATH) and os.path.getsize(OUTPATH) > ROTATE_MAX:
                # rotate files: OUTPATH.1 .. OUTPATH.N
                for i in range(ROTATE_KEEP-1, 0, -1):
                    src = f"{OUTPATH}.{i}"
                    dst = f"{OUTPATH}.{i+1}"
                    if os.path.exists(src):
                        os.replace(src, dst)
                os.replace(OUTPATH, f"{OUTPATH}.1")
        except Exception as exc:
            print('rotate failed', exc)
        print('received alert:', ','.join([a.get('labels', {}).get('alertname','') for a in data.get('alerts',[])]), 'count:', len(data.get('alerts',[])))
        self.send_response(200)
        self.end_headers()


def run(host='0.0.0.0', port=5001):
    srv = HTTPServer((host, port), ReceiverHandler)
    print(f'Alert receiver listening on http://{host}:{port}/alert')
    try:
        srv.serve_forever()
    finally:
        srv.server_close()


if __name__ == '__main__':
    run()
