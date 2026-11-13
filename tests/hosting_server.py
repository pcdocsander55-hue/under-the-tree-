"""Local stand-in for Firebase Hosting: serves web/dist with the rewrites and headers from firebase.json."""
import http.server, json, pathlib, re, sys, threading
ROOT = pathlib.Path(__file__).resolve().parent.parent
def glob_re(g):
    out, i = '', 0
    while i < len(g):
        if g.startswith('**', i): out += '.*'; i += 2
        elif g.startswith('@(', i): j = g.index(')', i); out += '(' + g[i+2:j].replace('.', r'\.') + ')'; i = j + 1
        elif g[i] == '*': out += '[^/]*'; i += 1
        else: out += re.escape(g[i]); i += 1
    return re.compile('^' + out + '$')
def make_handler(dist, cfg):
    rules = [(glob_re(h['source'] if h['source'].startswith('/') or h['source'] == '**' else '/' + h['source']), h['headers']) for h in cfg['hosting']['headers']]
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(s, *a, **k): super().__init__(*a, directory=str(dist), **k)
        def log_message(s, *a): pass
        def send_head(s):
            p = s.path.split('?')[0]
            f = dist / p.lstrip('/')
            if p == '/' or not f.exists() or f.is_dir(): s.path = '/index.html' + ('?' + s.path.split('?', 1)[1] if '?' in s.path else '')
            return super().send_head()
        def end_headers(s):
            p = s.path.split('?')[0]
            for rx, hs in rules:
                if rx.match(p) or rx.pattern == '^.*$':
                    for h in hs: s.send_header(h['key'], h['value'])
            super().end_headers()
        def guess_type(s, path):
            return 'application/manifest+json' if str(path).endswith('.webmanifest') else super().guess_type(path)
    return H
def serve(port=8765, dist=None):
    cfg = json.loads((ROOT / 'firebase.json').read_text())
    dist = pathlib.Path(dist or ROOT / cfg['hosting']['public'])
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), make_handler(dist, cfg))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
if __name__ == '__main__':
    serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8765); print('serving'); threading.Event().wait()
