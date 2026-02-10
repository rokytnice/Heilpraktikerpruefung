---
description: Verify the quiz functionality by running it in the emulator and checking results.
---

// turbo-all
1. Ensure the emulator is running and the app is built:
   - Run `./gradlew assembleDebug`
   - Run `adb wait-for-device`

2. Install and launch the app:
   - Run `adb install -r app/build/outputs/apk/debug/app-debug.apk`
   - Run `adb shell am start -n com.example.heilpraktikerpruefung/.MainActivity`
   - Wait for launch: `sleep 5`

3. Perform automated quiz interaction (Mocking first question answer):
   - Navigate to quiz: `adb shell input tap 300 300` (Assumes first exam is around there)
   - Select option A: `adb shell input tap 300 500`
   - Click "Prüfen": `adb shell input tap 300 1000`
   - Click "Nächste Frage": `adb shell input tap 300 1100`

4. Capture result for verification:
   - `adb shell screencap -p /sdcard/quiz_test.png`
   - `adb pull /sdcard/quiz_test.png .`

5. Check logs for errors:
   - `adb logcat -d | grep "com.example.heilpraktikerpruefung"`
