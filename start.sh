# Check that machine name matches parameter supplied.
# Check whether required process is running. Start if not
# 29 October 2025

# Assume we want to run startup apps if no parameter supplied
# if [ "$1" = "" ] ; then hostname=${HOSTNAME%%.*} ; else hostname=$1 ; fi
#
# if [ "$HOSTNAME" = "$hostname.ecs.vuw.ac.nz" ] ; then
#     PROCESS_NAME="vncviewer"
#     COMMAND_TO_RUN="echo $1 not running" # Replace with the command to execute
#     if ! pgrep -x "$PROCESS_NAME" > /dev/null; then
#         echo "$PROCESS_NAME is not running. Starting startup systems now..."
#         vncviewer regent:22 > /dev/null 2>&1  &
#         okular /home/stevecos/Documents/techstillmore/Contiki-NG-Flowcharts2.pdf /home/stevecos/Documents/techstillmore/occurences+refactoring.pdf /home/stevecos/Documents/techstillmore/Contiki-NG-Flowcharts.pdf /home/stevecos/Documents/techstillmore/Contiki-NG_TwoDODAG.pdf /home/stevecos/data/SimSummary.pdf  > /dev/null 2>&1  &
#     else
#         echo "$PROCESS_NAME is already running."
#     fi
# else
#     echo "Not logging into $1 so not running startup"
# fi
