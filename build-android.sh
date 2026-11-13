#!/usr/bin/env bash
# Build Under the Tree 0.10.1 Android APK without Gradle.
# Requires a JDK plus Android SDK platform 23 and a build-tools release containing aapt, d8, zipalign and apksigner.
# The shared app core is copied from shared/index.html into the APK at build time.
#
# Public build (unsigned): ./build-android.sh
# Optional signing with your own key:
#   KEYSTORE=/path/key.jks KEY_ALIAS=undertree KEYSTORE_PASS='...' KEY_PASS='...' ./build-android.sh
# The project's original release signing key is intentionally NOT in this repository.
set -euo pipefail
cd "$(dirname "$0")"
VERSION=0.10.1
VERSION_CODE=15
SDK="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
[ -n "$SDK" ] || { echo "Set ANDROID_SDK_ROOT or ANDROID_HOME."; exit 1; }
PLATFORM="$SDK/platforms/android-23/android.jar"
[ -f "$PLATFORM" ] || { echo "Missing platforms;android-23 ($PLATFORM)."; exit 1; }
BT="$(find "$SDK/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -1)"
[ -n "$BT" ] || { echo "No Android build-tools found."; exit 1; }
for t in aapt d8 zipalign; do [ -x "$BT/$t" ] || { echo "Missing $BT/$t"; exit 1; }; done
AAPT="$BT/aapt"; D8="$BT/d8"; ZIPALIGN="$BT/zipalign"; APKSIGNER="$BT/apksigner"
CORE=shared/index.html
[ -f "$CORE" ] || { echo "Missing $CORE"; exit 1; }
grep -q "const APP_VERSION = '$VERSION';" "$CORE" || { echo "shared/index.html is not $VERSION"; exit 1; }
grep -q "android:versionCode=\"$VERSION_CODE\"" android/AndroidManifest.xml || { echo "Manifest versionCode mismatch"; exit 1; }
grep -q "android:versionName=\"$VERSION\"" android/AndroidManifest.xml || { echo "Manifest versionName mismatch"; exit 1; }
grep -q "appVersion() { return \"$VERSION\"; }" android/src/com/undertree/family/MainActivity.java || { echo "MainActivity version mismatch"; exit 1; }
OUT=build/android
rm -rf "$OUT"
mkdir -p "$OUT/gen" "$OUT/classes" "$OUT/dex" "$OUT/assets/www"
cp "$CORE" "$OUT/assets/www/index.html"
"$AAPT" package -f -m -M android/AndroidManifest.xml -S android/res -A "$OUT/assets" -I "$PLATFORM" -J "$OUT/gen" -F "$OUT/unsigned.apk"
javac -source 8 -target 8 -bootclasspath "$PLATFORM" -Xlint:-options -encoding UTF-8 -d "$OUT/classes" $(find android/src "$OUT/gen" -name '*.java')
jar cf "$OUT/classes.jar" -C "$OUT/classes" .
"$D8" --min-api 23 --output "$OUT/dex" "$OUT/classes.jar"
( cd "$OUT" && "$AAPT" add unsigned.apk dex/classes.dex >/dev/null )
"$ZIPALIGN" -f -p 4 "$OUT/unsigned.apk" "$OUT/UnderTheTree-$VERSION-unsigned.apk"
echo "Unsigned APK: $OUT/UnderTheTree-$VERSION-unsigned.apk"
if [ -n "${KEYSTORE:-}" ]; then
  : "${KEY_ALIAS:?Set KEY_ALIAS}" "${KEYSTORE_PASS:?Set KEYSTORE_PASS}"
  KP="${KEY_PASS:-$KEYSTORE_PASS}"
  [ -x "$APKSIGNER" ] || { echo "Missing $APKSIGNER"; exit 1; }
  "$APKSIGNER" sign --ks "$KEYSTORE" --ks-key-alias "$KEY_ALIAS" --ks-pass "pass:$KEYSTORE_PASS" --key-pass "pass:$KP" --min-sdk-version 23 --out "$OUT/UnderTheTree-$VERSION.apk" "$OUT/UnderTheTree-$VERSION-unsigned.apk"
  "$APKSIGNER" verify --verbose --print-certs "$OUT/UnderTheTree-$VERSION.apk"
  echo "Signed APK: $OUT/UnderTheTree-$VERSION.apk"
fi
