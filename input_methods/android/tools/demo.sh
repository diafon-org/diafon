#!/bin/sh
# Device pass on an emulator: boot, install, enable and select Diafon, open a
# form with text fields, type through the IME, screenshot.
#   sh tools/demo.sh app/build/outputs/apk/debug/app-debug.apk
# Needs ANDROID_HOME with platform-tools, emulator and the android-35
# google_apis arm64 system image (see README, Build).
set -e
export ANDROID_HOME=${ANDROID_HOME:-$HOME/Library/Android/sdk}
export PATH=$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH
AVD=diafon
OUT=${OUT:-/tmp/diafon-demo}
mkdir -p "$OUT"
AVDM=$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager
if ! $AVDM list avd | grep -q "Name: $AVD"; then
  echo no | $AVDM create avd -n $AVD -k "system-images;android-35;google_apis;arm64-v8a" -d pixel_7 --force
fi
if ! adb get-state >/dev/null 2>&1; then
  nohup emulator -avd $AVD -no-window -no-audio -no-boot-anim -gpu swiftshader_indirect > "$OUT/emulator.log" 2>&1 &
fi
adb wait-for-device
until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do sleep 3; done
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0
adb install -r "$1"
adb shell pm clear io.diafon.ime >/dev/null      # defaults: a fresh install
adb shell ime enable io.diafon.ime/.DiafonIme
adb shell ime set io.diafon.ime/.DiafonIme
adb shell am force-stop com.google.android.contacts
adb shell am start -W -a android.intent.action.INSERT -t vnd.android.cursor.dir/contact >/dev/null
sleep 3
adb shell input tap 535 943            # First name (Pixel 7, 1080x2400)
sleep 1.5
adb shell input text "sjok%ssewp%snjawr"
sleep 0.5
adb exec-out screencap -p > "$OUT/script.png"
adb shell uiautomator dump /sdcard/ui.xml >/dev/null
adb shell cat /sdcard/ui.xml | grep -o 'text="[^"]*" [^>]*EditText' | head -1
echo "expected: șok sép ņár (web letters) · screenshot: $OUT/script.png"
# the candidate strip mid-word, then the setup screen
adb shell input text "%stxy"
sleep 1
adb exec-out screencap -p > "$OUT/strip.png"
adb shell input text "%s"
adb shell am start -W -n io.diafon.ime/.SettingsActivity >/dev/null
sleep 2
adb exec-out screencap -p > "$OUT/settings.png"
echo "strip: $OUT/strip.png · settings: $OUT/settings.png"

