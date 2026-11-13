"""Web release security scan. Exits non-zero on any finding (fail loud)."""
import pathlib, re, sys, json
ROOT = pathlib.Path(__file__).resolve().parent.parent; DIST = ROOT / 'web' / 'dist'
F = []; I = []
def bad(m): F.append(m)
files = [p for p in DIST.rglob('*') if p.is_file()]
for p in files:
    rel = p.relative_to(DIST).as_posix()
    if re.search(r'\.(jks|keystore|p12|pem|key|der|apk|zip|rules|env)$', rel, re.I): bad('forbidden file type: ' + rel)
    if p.suffix in ('.png',): continue
    t = p.read_text(encoding='utf-8', errors='replace')
    for rx, why in [(r'BEGIN (RSA |EC )?PRIVATE KEY', 'private key'), (r'"type"\s*:\s*"service_account"', 'service account JSON'),
                    (r'private_key_id', 'service account key id'), (r'storePassword|keyPassword|keystore', 'signing/keystore reference'),
                    (r'UTT2-[A-Za-z0-9_-]{20,}', 'a real UTT2 invite code'), (r'google-analytics|googletagmanager|gtag\(|firebase-analytics|getAnalytics|doubleclick|connect\.facebook|fbq\(|mixpanel|segment\.io|amplitude|hotjar|sentry', 'analytics/tracking'),
                    (r'console\.log\(', 'console.log (possible private identifiers)'), (r'\b(Heather|Steven)\b', 'a real family first name')]:
        for m in re.finditer(rx, t, re.I if why.startswith('analytics') else 0): bad('%s in %s: %r' % (why, rel, t[max(0, m.start()-30):m.end()+30]))
    for k in re.findall(r'AIza[0-9A-Za-z_-]{20,60}', t): I.append('%s: Firebase Web API key %s… (public client config by design; access is controlled by Firestore rules)' % (rel, k[:10]))
    for h in sorted(set(re.findall(r'https?://([a-z0-9.-]+\.[a-z]{2,})', t))):
        if h not in {'firestore.googleapis.com', 'identitytoolkit.googleapis.com', 'securetoken.googleapis.com', 'www.target.com', 'www.w3.org'}:
            I.append('%s: mentions host %s' % (rel, h))
sw = (DIST / 'service-worker.js').read_text()
if "url.origin !== self.location.origin) return" not in sw: bad('service worker may handle cross-origin requests')
shell = json.loads(re.search(r'const SHELL = (\[.*?\]);', sw).group(1))
if any(re.search(r'googleapis|firestore|http', s) for s in shell): bad('non-static entry in SW shell: %s' % shell)
print('SECURITY SCAN of', DIST); print('files:', len(files))
for i in I: print('INFO', i)
for f in F: print('FINDING', f)
print('RESULT:', 'FAIL' if F else 'PASS', '(%d findings)' % len(F)); sys.exit(1 if F else 0)
