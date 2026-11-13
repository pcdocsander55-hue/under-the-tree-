# Deploying the Under the Tree web / PWA (Firebase Hosting only)

**Target:** existing project `under-the-tree-1ee02`, default Hosting site → `https://under-the-tree-1ee02.web.app` (also `.firebaseapp.com`).
**Not deployed from here:** this container had no Firebase credentials and no network route to Google, so nothing is live yet.

## One-time setup (a PC where you can run Node — not required on a work PC)
1. Install Node.js LTS, then: `npm install -g firebase-tools`
2. `firebase login` (the Google account that owns the project)
3. Unzip the source package; open a terminal in the folder that contains `firebase.json`.
4. `firebase projects:list` — confirm `under-the-tree-1ee02` is listed.

## Deploy — Hosting ONLY
```
python3 tools/build_web.py          (optional: rebuilds web/dist from shared/ + web/; dist is already built)
python3 tools/security_scan.py      (must print RESULT: PASS)
firebase deploy --only hosting --project under-the-tree-1ee02
```
**Never** run plain `firebase deploy`, and never add `firestore` to `--only`. This `firebase.json` has no `firestore` section, so a bare deploy would not push rules either, but keep the habit. No Firestore data is read, written or migrated by a Hosting deploy.

Preview first if you like: `firebase hosting:channel:deploy preview --project under-the-tree-1ee02` gives a temporary URL that expires after 7 days.

## After deploying
- Open the URL, Settings → About: build number must match `web/dist/pwa.js` (`0.10.1-9c051de246` for this package).
- Hosting → Release history in the Firebase console lets you roll back one click.

## Check once in Google Cloud (not changed by me)
- **Firebase Web API key restrictions** (Cloud Console → APIs & Services → Credentials). If the key is restricted by *HTTP referrer*, add `under-the-tree-1ee02.web.app/*` and `under-the-tree-1ee02.firebaseapp.com/*`. If it's restricted to *Android apps*, the web version will be refused — but the APK sends no Android identity headers, so a restriction like that would already break Android; most likely it's unrestricted or API-restricted, which works as is.
- **Anonymous sign-in** stays enabled (it already is, Android uses it). Auth "Authorized domains" does not apply to anonymous REST sign-up.

## What the Hosting config does
- Every path serves `index.html` (single-page app).
- `index.html`, `service-worker.js`, `pwa.js`, `pwa.css`, manifest: `no-cache`, so updates are seen on next check.
- Content-Security-Policy: the page may only talk to `firestore.googleapis.com`, `identitytoolkit.googleapis.com`, `securetoken.googleapis.com`; images from any https site (product photos); no frames, no plugins. Also `Referrer-Policy: no-referrer` (retailers don't learn which page a photo came from).

## Rolling out an update
Change `shared/` or `web/`, run the build (build number changes automatically), deploy Hosting. Installed apps show "An Under the Tree update is ready." the next time they check (on launch, or on returning to the app after 30 minutes).
