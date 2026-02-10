#!/bin/bash

# Ensure the gradlew script is executable
chmod +x gradlew

# Run the Gradle task to install the debug APK
# This will build the APK and install it on the connected device
./gradlew installDebug
