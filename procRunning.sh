
# Proc Running - Test whether process named in parameter is running
# Output a message with the result
# 29 October 2025 Steve Cosgrove

PROCESS_NAME="$1" # Replace with the actual process name
COMMAND_TO_RUN="echo $1 not running" # Replace with the command to execute

if ! pgrep -x "$PROCESS_NAME" > /dev/null; then
  echo "$PROCESS_NAME is not running. Starting it now..."
  $COMMAND_TO_RUN &
else
  echo "$PROCESS_NAME is already running."
fi
