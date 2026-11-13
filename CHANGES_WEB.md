# Changes — Under the Tree 0.10.1 Web / PWA (build 0.10.1-9c051de246)

## Statements
- **Firestore rules: NOT changed.** `baseline/firestore-0_10_1.rules` is byte-identical to the uploaded file (sha256 `7bd6f6c2…856f27`). No web behaviour needed a rule change.
- **Android APK: NOT changed and NOT rebuilt.** Rebuilding needs your original signing key, which I don't have and must not replace.
- **Android code (shared core): changed in 7 places**, all listed below. On the Android path they are inert except #2, which fixes a crash. Proven only in Chromium with a fake Android bridge (12/12 identical screens), not in a real WebView. When you next build the APK, use `shared/index.html` as the WebView asset — I don't have your `build.sh`, so check its source path.
- **Firebase project:** same one, `under-the-tree-1ee02`. No new project, no separate Apple families, no data model change.
- **No analytics, ads, trackers or telemetry added.** Security scan checks for them.

## Defect found in 0.10.1 (affects the installed Android app)
Settings → child → setup code → **Copy** throws: the handler calls `Platform.copyText`, which does not exist (`Platform.copy` does). The code still shows on screen, so it can be read out; the button just fails. Confirmed by running the 0.10.1 asset. Fixed in the shared core (edit #2); reaches Android only after a signed rebuild.

## Shared core edits (`tools/patch_core.py`, full diff in `docs/core.diff`)
1. `Platform.isWeb` — true only when the web adapter set `window.UTT_WEB`. Never true on Android.
2. `Platform.copyText` added (the fix above). Web copy uses the Clipboard API on https; if it fails later, a toast says so.
3. Settings → About: "Under the Tree 0.10.1 / Web / PWA (installed | in the browser), build …". Android text unchanged.
4. Fill from link on the web: "We couldn't fill this item automatically. You can still enter the details below." No scraping attempt, no proxy.
5. Boot: in the web build only, opening scene + music wait for the first "Enter" tap (shown only if music is on). Android boot unchanged.
6. `sheetOpen` exposed so the update prompt never reloads over an open form.
7. A family member's first name in a code comment replaced with generic wording (the web bundle is public).

## Web-only additions (`web/`)
- `pwa.js` — install help (iPhone/iPad, hidden once installed, "Got it" hides 14 days, "Don't show again" forever); Enter screen; service-worker registration; update check on launch and on return after 30 min; "An Under the Tree update is ready. [Update] [Later]"; asks the browser to keep storage once joined.
- `pwa.css` — safe areas on all four sides (header, tabs, add button, sheets, toasts), `100dvh` sheets, no double-tap zoom delay.
- `service-worker.template.js` — caches exactly 10 static shell files per build; ignores every cross-origin request (Firebase, retailer images), so no family data can enter its cache; old caches deleted on update; waits for the person to tap Update.
- `manifest.webmanifest`, `head-inject.html`, icons (180/192/512/maskable 512/64 favicon, redrawn from the Android launcher design).
- `firebase.json` / `.firebaserc` — Hosting only, SPA rewrite, cache headers, strict CSP.
- `tools/build_web.py` (fails on missing key, missing asset, unreplaced placeholder), `tools/security_scan.py` (fails on any finding).

## Remaining Safari / iOS limitations
- **Safari and the Home Screen app keep separate storage.** Joining in Safari then installing means joining again in the app (pick yourself — it moves you, no duplicate). Install help says "install first".
- **If iOS deletes the site's storage** (rare for installed apps; possible for plain Safari tabs unused for weeks), the app shows the normal join screen. Rejoining and picking yourself moves your profile; typing your name under "I'm new" would create a second you. The app does not guess.
- **Home Screen label** is likely truncated ("Under the T…") — iOS limit; name kept as specified.
- **Music** needs the Enter tap each cold launch and follows the silent switch. The Android custom-song feature doesn't exist on web (the carol plays instead).
- **Fill from link** is Android-only. A future safe option is a small authenticated server-side lookup (e.g. a Cloud Function limited to family members) — not built, would need the Blaze plan and conflicts with the no-recurring-cost goal.
- **Share-to-app** (sharing a product link *into* Under the Tree from another app) is Android-only; iOS PWAs can't receive shares.
- **Local family snapshot:** like Android, the last loaded family view is kept in the device's storage for offline viewing. On a shared iPad, the next person could see what the last one could (never the recipient's own ideas, which are never downloaded).
- **Not proven on Safari:** everything in WEB_TEST_RESULTS.txt ran in Chromium. REAL_IPHONE_TEST.md is the proof step.
