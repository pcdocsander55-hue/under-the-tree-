"""Android code path check: runs the 0.10.1 APK asset and the new shared core side by side inside Chromium with a
fake Android bridge (window.UTTNative), drives the same steps, and compares what each shows.
This proves the web edits are inert on the Android path; it is NOT a test on a real Android WebView."""
import sys, json, pathlib, re
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from playwright.sync_api import sync_playwright
from mock_firestore import MockFirebase
import http.server, threading
ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIDGE = r"""
window.__store = {}; window.__copied = [];
window.UTTNative = {
  getItem: k => (k in __store ? __store[k] : null), setItem: (k, v) => { __store[k] = String(v); return true; }, removeItem: k => { delete __store[k]; },
  request: (id, m, url, h, body) => { fetch(url, {method: m, headers: JSON.parse(h), body: body === '' ? undefined : body})
      .then(r => r.text().then(t => window.UTT_onNative(id, JSON.stringify({status: r.status, body: t, finalUrl: url}))))
      .catch(e => window.UTT_onNative(id, JSON.stringify({error: String(e)}))); },
  openExternal: u => {}, shareText: t => {}, copyText: t => { __copied.push(t); return true; }, consumeSharedText: () => ''
};"""
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(s, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8766), lambda *a, **k: Q(*a, directory=str(ROOT), **k))
threading.Thread(target=srv.serve_forever, daemon=True).start()
R = []
def check(n, ok, d=''): R.append({'test': n, 'result': 'PASS' if ok else 'FAIL', 'detail': str(d)[:300]}); print(('PASS ' if ok else 'FAIL ') + n + ('' if ok else ' :: ' + str(d)[:300]))
def run(b, path):
    fb = MockFirebase(); c = b.new_context(viewport={'width': 390, 'height': 844}); c.add_init_script(BRIDGE)
    c.route('https://*.googleapis.com/**', fb.route); pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8766/' + path); pg.wait_for_timeout(600); shots = {}
    shots['gate'] = pg.locator('.utt-gate').count(); shots['welcome'] = pg.inner_text('#app'); shots['music'] = pg.evaluate('UTT.music.plays')
    pg.click('[data-act="setup:start"]'); pg.fill('input[name=familyName]', 'Fam'); pg.fill('form[data-form=start] input[name=name]', 'Dad')
    pg.click('form[data-form=start] button[type=submit]'); pg.wait_for_timeout(1000)
    sett = re.sub(r'UTT2-\S+', 'UTT2-X', pg.inner_text('main')); shots['settings'] = sett
    pg.click('[data-act="invite:copy"]'); shots['copied'] = pg.evaluate('__copied.length')
    pg.click('.nav [data-tab="mine"]'); pg.wait_for_timeout(200); shots['mine'] = pg.inner_text('main')
    pg.click('[data-act="wish:new"] >> nth=0'); pg.fill('#wishForm input[name=title]', 'Socks'); pg.click('#wishForm button[type=submit]'); pg.wait_for_timeout(600)
    shots['mine2'] = pg.inner_text('main'); shots['errors'] = errs
    shots['copyText'] = pg.evaluate("() => { try { return UTT.Platform.copyText('x'); } catch(e){ return 'THREW ' + e.message; } }")
    shots['isWeb'] = pg.evaluate('UTT.Platform.isWeb === true'); c.close(); return shots
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    old = run(b, 'baseline/index-0.10.1-from-apk.html'); new = run(b, 'shared/index.html'); b.close()
for k in ['gate', 'welcome', 'music', 'mine', 'mine2', 'copied']:
    check('Android path: "%s" identical to the 0.10.1 APK asset' % k, old[k] == new[k], (old[k], new[k]))
check('Android path: Settings identical except build info (none on Android)', old['settings'] == new['settings'], [l for l in new['settings'].splitlines() if l not in old['settings'].splitlines()])
check('Android path: no Enter screen, music starts at launch as before', new['gate'] == 0 and new['music'] == old['music'])
check('Android path: web flag is off', new['isWeb'] is False)
check('0.10.1 APK asset: Platform.copyText missing (the setup-code Copy bug)', str(old['copyText']).startswith('THREW'), old['copyText'])
check('shared core: Platform.copyText works through the Android bridge', new['copyText'] is True, new['copyText'])
check('no page errors on either', not old['errors'] and not new['errors'], (old['errors'], new['errors']))
json.dump(R, open(ROOT / 'tests' / 'results_android_path.json', 'w'), indent=1)
print('%d checks, %d failed' % (len(R), len([r for r in R if r['result'] == 'FAIL'])))
