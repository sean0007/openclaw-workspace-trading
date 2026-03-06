#!/usr/bin/env python3
"""Simple HTTP webhook receiver for Alertmanager alerts.

Writes incoming alerts as JSON lines to /tmp/alertmanager_received.jsonl and
prints a short log to stdout. Used for local testing of Alertmanager webhook
delivery.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

OUTPATH = '/tmp/alertmanager_received.jsonl'


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
        # append to file
        try:
            with open(OUTPATH, 'a') as f:
                f.write(json.dumps(data) + '\n')
        except Exception as exc:
            print('write failed', exc)
        print('received alert:', ','.join([a.get('labels', {}).get('alertname','') for a in data.get('alerts',[])]))
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
