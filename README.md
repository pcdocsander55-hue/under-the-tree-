# Under the Tree

Private staging repository for the family Christmas wish-list app.

## Current source snapshot

This repository starts from the verified **0.10.1 shared Android/Web/PWA source package**. The UPC/barcode scanner was **not implemented**.

- `shared/index.html` — shared app core
- `web/` — Web/PWA adapter and assets
- `baseline/` — 0.10.1 comparison baseline and Firestore rules
- `tools/` — build, patch, icon, and security utilities
- `tests/` — automated Web/Android-path test code
- `firebase.json` / `.firebaserc` — Hosting configuration

The Android wrapper source (Java/build scripts) is not present in this source snapshot. The existing Android APK was built separately.

## Security

Do **not** commit the Android signing keystore, signing-key ZIP, passwords, service-account credentials, or other private secrets.

The Firebase Web API key used by the Web/PWA client is public client configuration; access control is enforced by Firebase Authentication and Firestore security rules.

## License

No open-source license has been selected yet. Until one is added, no license is granted to copy, modify, or redistribute this source.
