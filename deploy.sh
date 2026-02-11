#!/bin/bash
set -e

cd "$(dirname "$0")"

APK="app/build/outputs/apk/debug/app-debug.apk"

# Build
echo "Building APK..."
./gradlew assembleDebug -q

if [ ! -f "$APK" ]; then
    echo "Fehler: APK wurde nicht erstellt."
    exit 1
fi

# List devices
DEVICES=()
while IFS= read -r line; do
    serial=$(echo "$line" | awk '{print $1}')
    state=$(echo "$line" | awk '{print $2}')
    if [ "$state" = "device" ]; then
        model=$(adb -s "$serial" shell getprop ro.product.model 2>/dev/null | tr -d '\r')
        DEVICES+=("$serial|$model")
    fi
done < <(adb devices | tail -n +2 | grep -v '^$')

if [ ${#DEVICES[@]} -eq 0 ]; then
    echo "Keine Geräte gefunden."
    exit 1
fi

echo ""
echo "Verfügbare Geräte:"
echo ""
echo "  0) Alle (Standard)"
for i in "${!DEVICES[@]}"; do
    serial="${DEVICES[$i]%%|*}"
    model="${DEVICES[$i]#*|}"
    echo "  $((i+1))) $model ($serial)"
done
echo ""
read -t 5 -p "Gerät wählen [0-${#DEVICES[@]}] (Standard: Alle in 5s): " choice || choice=0
echo ""

if [ -z "$choice" ] || [ "$choice" = "0" ]; then
    for entry in "${DEVICES[@]}"; do
        serial="${entry%%|*}"
        model="${entry#*|}"
        echo "Installiere auf $model ($serial)..."
        adb -s "$serial" install -r "$APK"
        adb -s "$serial" shell am start -n com.example.heilpraktikerpruefung/.MainActivity
    done
else
    if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt ${#DEVICES[@]} ]; then
        echo "Ungültige Auswahl."
        exit 1
    fi
    SELECTED="${DEVICES[$((choice-1))]%%|*}"
    MODEL="${DEVICES[$((choice-1))]#*|}"
    echo "Installiere auf $MODEL ($SELECTED)..."
    adb -s "$SELECTED" install -r "$APK"
    adb -s "$SELECTED" shell am start -n com.example.heilpraktikerpruefung/.MainActivity
fi
echo "Fertig!"
