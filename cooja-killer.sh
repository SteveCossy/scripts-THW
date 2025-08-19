#!/bin/bash

# A script to safely find and terminate all Java processes
# related to the Contiki-NG Cooja simulator for the current user.

echo "--- Finding Cooja Simulator Java Processes ---"

# We use pgrep for a safer and cleaner way to find the PIDs.
# It's better than parsing the output of 'ps'.

# Find the PID of the Gradle Wrapper. We look for a Java process
# running the specific 'gradle-wrapper.jar'.
GRADLE_WRAPPER_PID=$(pgrep -f "java.*gradle-wrapper.jar.*run")

# Find the PID of the Cooja GUI application. We look for a Java
# process running 'org.contikios.cooja.Main'.
COOJA_GUI_PID=$(pgrep -f "java.*org.contikios.cooja.Main")

# --- Safety Check ---
# Check if we actually found the PIDs before trying to kill them.

if [ -z "$GRADLE_WRAPPER_PID" ] && [ -z "$COOJA_GUI_PID" ]; then
    echo "No running Cooja processes found. Exiting."
    exit 0
fi


# --- Termination ---
# We kill the processes in a specific order: GUI first, then the wrapper.

if [ -n "$COOJA_GUI_PID" ]; then
    echo "Attempting to kill Cooja GUI (PID: $COOJA_GUI_PID)..."
    kill -9 "$COOJA_GUI_PID"
    if [ $? -eq 0 ]; then
        echo "Successfully killed Cooja GUI."
    else
        echo "Failed to kill Cooja GUI (PID: $COOJA_GUI_PID). It might already be gone."
    fi
else
    echo "Cooja GUI process not found."
fi

echo "" # Add a blank line for readability

if [ -n "$GRADLE_WRAPPER_PID" ]; then
    echo "Attempting to kill Gradle Wrapper (PID: $GRADLE_WRAPPER_PID)..."
    kill -9 "$GRADLE_WRAPPER_PID"
    if [ $? -eq 0 ]; then
        echo "Successfully killed Gradle Wrapper."
    else
        echo "Failed to kill Gradle Wrapper (PID: $GRADLE_WRAPPER_PID). It might already be gone."
    fi
else
    echo "Gradle Wrapper process not found."
fi

echo ""
echo "--- Cooja cleanup complete. ---"

# Optional: Add the command to restart the simulator right here
# echo "Restarting Cooja..."
# cd /home/stevecos/contiki-ng/tools/cooja && ./gradlew run
