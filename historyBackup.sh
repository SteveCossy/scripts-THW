# Send recent history to long-term backup
# Steve Cosgrove updated 30 June 2025

if [ "$#" -eq 0 ]; then
  echo "Syntax $0 <nbr of lines to save>"
else
  TODAY=---`date +%F`---

  logFileName=/home/stevecos/Documents/technotes/history.txt

  echo $TODAY >>$logFileName
  history | tail -$1 >>$logFileName

fi

tail -$(( $1 + 5 )) $logFileName
