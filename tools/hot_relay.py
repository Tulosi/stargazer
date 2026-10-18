#!/usr/bin/env python3
"""
Tiny local relay so saved_posts_browser.html can read Reddit's real hot feed.

Browsers are not allowed to call reddit.com directly (no CORS headers). This script runs on
your own computer, fetches https://www.reddit.com/r/<subs>/hot.json for the page, and hands the
answer back with CORS enabled. It also serves the page itself.

    python hot_relay.py            # then open http://localhost:8765
    python hot_relay.py 9000       # use another port

The page also finds the relay when you open the .html file straight from disk, as long as this
script is running on port 8765. No accounts, keys or packages needed (Python 3.7+).
Set REDDIT_USERNAME to put your name in the User-Agent, which Reddit asks for.
"""
import sys, os, re, urllib.request, urllib.error, urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
UPSTREAM = os.environ.get("RELAY_UPSTREAM", "https://www.reddit.com")   # overridable for testing
UA = "web:saved-posts-viewer:v1.0 (personal use; by /u/%s)" % os.environ.get("REDDIT_USERNAME", "unknown")
SUBS = re.compile(r"^[A-Za-z0-9_]{1,40}(\+[A-Za-z0-9_]{1,40}){0,99}$")
AFTER = re.compile(r"^t3_[a-z0-9]{1,12}$")

class H(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def reply(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/":
            self.path = "/saved_posts_browser.html"
        m = re.match(r"^/relay/hot/([^/]+)$", u.path)
        if not m:
            return super().do_GET()
        subs = urllib.parse.unquote(m.group(1))
        q = urllib.parse.parse_qs(u.query)
        after = (q.get("after") or [""])[0]
        if not SUBS.match(subs) or (after and not AFTER.match(after)):
            return self.reply(400, b'{"error":"bad request"}')
        url = "%s/r/%s/hot.json?limit=100&raw_json=1%s" % (UPSTREAM, subs, "&after=" + after if after else "")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return self.reply(r.status, r.read())
        except urllib.error.HTTPError as e:
            return self.reply(e.code, e.read() or b"{}")
        except Exception as e:
            return self.reply(502, ('{"error":"%s"}' % str(e).replace('"', "'")).encode())

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Serving on http://localhost:%d  (Ctrl+C to stop)" % PORT)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
