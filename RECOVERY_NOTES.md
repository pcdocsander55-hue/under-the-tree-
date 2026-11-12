# Under the Tree — recovered 0.10.1 web source

This package was extracted from the supplied `UnderTheTree-0.10.1.apk`. It is **not** a complete Android Studio project and **not** an installable Android update.

## Verified contents

- `shared/index.html`: self-contained HTML, CSS, JavaScript app recovered verbatim except for the **one confirmed setup-code Copy fix** below.
- `baseline/index.original.0.10.1.html`: exact original bundled HTML, retained for auditing and comparing changes.
- `web/icons/`: launcher PNG files extracted directly from the APK.
- `tests/check_recovery.js`: minimal static regression checks.
- `RECOVERY-MANIFEST.json`: file integrity and APK contents record.

## Confirmed bug (fixed in `shared/index.html`)

The `claimcode:copy` button handler called `Platform.copyText(...)`, but the `Platform` object defines `copy(...)` instead; it is the Android native bridge that defines `copyText`. The fix calls `Platform.copy(...)`, matching the working invite-code Copy handler. This avoids a JavaScript TypeError caused by the missing method.

## Limitations and next steps

1. The APK contains compiled `classes.dex`, but **no original Java/Gradle Android wrapper source**. The Android wrapper must be recovered separately or recreated and thoroughly tested.
2. The original Android app **did not include camera/barcode scanning**. That requires separate implementation and Android camera access decisions.
3. A replacement APK requires Android build tools and the **original signing key** if it is to update the existing installed app in place. Never store the signing key in GitHub.
4. The recovered/edited HTML has not been tested in the installed APK or against the live Firestore database. Verify family privacy, account claiming, syncing, network, invite sharing, music, and link handling on physical devices before release.
5. This bundle should remain private. It includes publicly usable Firebase web client settings but must not be treated as a server secret or proof of secure rules.

## Exact origin

The original APK is unchanged. Its SHA-256 is in `RECOVERY-MANIFEST.json`. No additional app features or changes are claimed.
