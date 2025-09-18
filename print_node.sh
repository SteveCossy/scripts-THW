echo $1
grep -nP '^(?=.*Pref Y)(?=.*Node:$1 )'  $2 | tail -1
