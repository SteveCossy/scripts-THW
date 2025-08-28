grep -nE "(DAO-SCHED|Sending a)" $1 | grep "Node:$2 " | grep -v DIO | grep -v DIS

