# Under the Tree — shared core + Android + Web/PWA (0.10.1)

```
shared/index.html          ONE app core (UI, styles, Firebase, wishes, Gift Ideas, Shopping, family, children, themes)
                           -> Android WebView asset AND the web app. Built from the 0.10.1 APK asset by tools/patch_core.py
web/                       web-only adapter: pwa.js, pwa.css, manifest, service-worker template, icons, head tags
web/dist/                  deploy-ready site (built by tools/build_web.py) — this is what Firebase Hosting serves
firebase.json, .firebaserc Hosting-only config for under-the-tree-1ee02
baseline/                  untouched 0.10.1 APK asset + 0.10.1 rules, for comparison
tools/                     patch_core.py, build_web.py, security_scan.py, make_icons.py
tests/                     test_web.py (77 checks), test_android_path.py (12 checks), local Hosting + Firebase stand-ins
docs/core.diff             every change to the shared core
```
Android wrapper source (Java, build.sh, signing) is **not** here — only the APK was provided. The Android side is unchanged.

Run the tests (needs Python 3 + Playwright + Chromium): `python3 tests/test_web.py` and `python3 tests/test_android_path.py`.
Docs: WEB_DEPLOYMENT.md, REAL_IPHONE_TEST.md, WEB_TEST_RESULTS.txt, CHANGES_WEB.md.
