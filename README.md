# Under the Tree

Private staging repository for the family Christmas wish-list app.

## Repository status

The repository is initialized and protected against accidental commits of signing keys and common private credentials.

The last source package I can independently verify from the project files is **0.10.1 shared Android/Web/PWA**. The UPC/barcode scanner was **not implemented**.

Before this repository is treated as the authoritative source, the **current tested source package** should be checked against that 0.10.1 snapshot and committed here. I do not want to silently publish an older snapshot if the tested build changed elsewhere.

## Expected project structure

- `shared/index.html` — shared app core
- `web/` — Web/PWA adapter and assets
- `baseline/` — comparison baseline and Firestore rules
- `tools/` — build, patch, icon, and security utilities
- `tests/` — automated Web/Android-path tests
- `firebase.json` / `.firebaserc` — Hosting configuration

The 0.10.1 source snapshot does **not** contain the Android wrapper source (Java/build scripts). The existing Android APK was built separately.

## Security

Do **not** commit the Android signing keystore, signing-key ZIP, passwords, service-account credentials, or other private secrets.

The Firebase Web API key used by the Web/PWA client is public client configuration; access control is enforced by Firebase Authentication and Firestore security rules.

## Public-release status

Keep this repository **private** until the final source, branding, third-party licensing, and secrets review is complete.

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0-only)**. You may use, study, modify, and redistribute the code under the terms of GPLv3. Distributed modified versions must remain under GPLv3 and include the corresponding source code.

See [LICENSE](LICENSE) for the full license text.
