# Helper script for finding parent tables from each node in my network
# Run with a command like this
# for i in {1..24} ; do /home/stevecos/scripts/listParents.sh $i /home/stevecos/Cooja/10-RPL-20250630135157.txt ; echo --- ; done | grep -E "Pref Y|Instance|---"


echo $1

#grep Parent $2 | grep "Node:$1 " | tail -30 | grep -E "Pref Y|Instance"
grep -n Parent $2 | grep "Node:$1 " | grep -E "Pref Y|Instance|Preferred" | tail -6
