#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Building debug APK..."
./gradlew assembleDebug

APK="app/build/outputs/apk/debug/app-debug.apk"

if [ -f "$APK" ]; then
    SIZE=$(du -h "$APK" | cut -f1)
    echo ""
    echo "APK erstellt: $APK ($SIZE)"
else
    echo "Fehler: APK wurde nicht erstellt."
    exit 1
fi
