# Android build

The Android app is a small native WebView wrapper around the shared `shared/index.html` app core.

Version **0.10.1** uses package `com.undertree.family`, versionCode **15**, minSdk 23 and targetSdk 34. The wrapper source was recovered from the verified 0.10.0 source and updated to 0.10.1; the shared core is the tested 0.10.1 core already in this repository.

## Build

Install a JDK and Android SDK components `platforms;android-23` plus a current `build-tools` package, set `ANDROID_SDK_ROOT`, then run:

```bash
./build-android.sh
```

That produces an unsigned APK. To sign a build, set `KEYSTORE`, `KEY_ALIAS`, `KEYSTORE_PASS`, and optionally `KEY_PASS` before running the script.

The original Under the Tree release keystore is deliberately **not** published. That private key is required only to install an update over copies signed by the original developer. Forks should sign with their own key.

## Published 0.10.1 APK

The public 0.10.1 APK uses the original release certificate with SHA-256:

`b4ccc272fae198e1fabb3a88b8102336285d41d68d5df1931bde5b71f7c4d640`

The APK includes the same `shared/index.html` core that is committed in this repository, including the setup-code Copy fix.
