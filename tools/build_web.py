"""Build web/dist from the shared core + web adapter. Fails loudly on anything unexpected."""
import hashlib, json, pathlib, re, shutil, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
CORE = ROOT / 'shared' / 'index.html'; WEB = ROOT / 'web'; DIST = WEB / 'dist'
def die(m): sys.exit('BUILD FAILED: ' + m)
core = CORE.read_text(encoding='utf-8')
m = re.search(r"const APP_VERSION = '([0-9.]+)';", core) or die('APP_VERSION not found')
version = m.group(1)
key = re.search(r"apiKey: '([^']*)'", core) or die('apiKey not found')
if not re.fullmatch(r'AIza[0-9A-Za-z_-]{20,60}', key.group(1)): die('Web API key missing/invalid in shared core')
if core.count('</head>') != 1: die('expected exactly one </head>')
STATIC = ['pwa.js', 'pwa.css', 'manifest.webmanifest', 'icons/apple-touch-icon.png', 'icons/icon-192.png',
          'icons/icon-512.png', 'icons/icon-maskable-512.png', 'icons/favicon-64.png']
for s in STATIC:
    if not (WEB / s).is_file(): die('missing web asset ' + s)
h = hashlib.sha256(core.encode())
for s in STATIC + ['head-inject.html', 'service-worker.template.js']: h.update((WEB / s).read_bytes())
build = version + '-' + h.hexdigest()[:10]
if DIST.exists(): shutil.rmtree(DIST)
(DIST / 'icons').mkdir(parents=True)
inject = (WEB / 'head-inject.html').read_text(encoding='utf-8').replace('__UTT_BUILD__', build)
(DIST / 'index.html').write_text(core.replace('</head>', inject + '</head>'), encoding='utf-8')
for s in STATIC:
    data = (WEB / s).read_bytes()
    if s == 'pwa.js': data = data.replace(b'__UTT_BUILD__', build.encode())
    (DIST / s).write_bytes(data)
shell = ['./', 'index.html'] + STATIC
sw = (WEB / 'service-worker.template.js').read_text(encoding='utf-8').replace('__UTT_BUILD__', build).replace('__UTT_SHELL__', json.dumps(shell))
(DIST / 'service-worker.js').write_text(sw, encoding='utf-8')
for f in DIST.rglob('*'):
    if f.is_file() and b'__UTT_' in f.read_bytes(): die('unreplaced placeholder in ' + str(f))
files = sorted(p for p in DIST.rglob('*') if p.is_file())
(DIST / 'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.relative_to(DIST).as_posix() + '\n' for p in files))
print('built', build, '->', DIST, '(%d files)' % len(files))
