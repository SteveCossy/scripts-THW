# Process a Contiki-NG log file
file=$1 
head -1 $file && ls -l $file
python3 /home/stevecos/Documents/references/parse_rpl_log.py $file | grep DAG

echo -n Hit enter to continue
# read

python3 /home/stevecos/Documents/references/parse_rpl_log.py $file

TODAY="$(date +%Y%m%d)"

ls rpl_graph_$TODAY*
ls rpl_table_$TODAY*
