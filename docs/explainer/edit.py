#!/usr/bin/env python3
"""Edit the explainer's words in the browser.

    python3 docs/explainer/edit.py        then open http://localhost:8000/ and press e

Serves docs/ (the built explainer.html). The page reads the live docs/explainer/text.md through
/text.json, and every edit is POSTed to /save (just the fields changed), which merges it into text.md (format: textfile.py).
After each save, explainer.html is rebuilt in the background (gendata.py, ~15-25 s), so the
committed page has the new words too. Ctrl-C to stop. Local use only: it binds to 127.0.0.1.
"""
import http.server
import json
import os
import subprocess
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import textfile  # noqa: E402

PORT = int(os.environ.get('PORT', 8000))


class Rebuild:
    """Run gendata.py after a save; saves during a run queue one more run."""
    def __init__(self):
        self.lock, self.running, self.again = threading.Lock(), False, False

    def kick(self):
        with self.lock:
            if self.running:
                self.again = True
                return
            self.running = True
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        while True:
            r = subprocess.run([sys.executable, os.path.join(HERE, 'gendata.py')], capture_output=True, text=True)
            print('rebuilt explainer.html' if r.returncode == 0 else 'gendata.py FAILED:\n' + r.stderr[-2000:], flush=True)
            with self.lock:
                if not self.again:
                    self.running = False
                    return
                self.again = False


rebuild = Rebuild()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=DOCS, **k)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.send_response(302)
            self.send_header('Location', '/explainer.html')
            self.end_headers()
            return
        if self.path.split('?')[0] == '/text.json':
            body = json.dumps(textfile.load()[1]).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_POST(self):
        if self.path != '/save':
            self.send_error(404)
            return
        try:
            pages = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
            assert isinstance(pages, dict) and all(isinstance(v, dict) for v in pages.values())
            textfile.save(pages)
        except Exception as e:  # bad request: leave text.md as it was
            self.send_error(400, str(e))
            return
        self.send_response(204)
        self.end_headers()
        print('saved text.md', flush=True)
        rebuild.kick()

    def log_message(self, fmt, *args):
        pass  # quiet: saves and rebuilds print their own line


if __name__ == '__main__':
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    print(f'http://localhost:{PORT}/  (press e on the page to edit; Ctrl-C to stop)', flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
