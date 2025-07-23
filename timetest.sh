# Time Test to learn how time works in a script
#

# Set a target in minutes
targetDate="$(date --date="5 minutes" +%s)"
echo $targetDate
date +%s

read

Now="$(date +%s)"

if [ ${Now} -gt ${targetDate} ]; then
   echo bye!
else
   echo too quick
fi

