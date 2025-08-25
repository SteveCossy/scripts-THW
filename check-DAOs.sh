# Checking contents of log files

echo -n "fd00 lines: "
grep -n "DAO lifetime:" $1 | grep "prefix: fd00" |  wc -l 
echo -n "fd02 lines: "
grep -n "DAO lifetime:" $1 | grep "prefix: fd02" |  wc -l
echo -n "fd00 lines also with fd02: "
grep -n "DAO lifetime:" $1 | grep "prefix: fd00" | grep fd02 | wc -l
echo -n "fd02 lines also with fd00: "
grep -n "DAO lifetime:" $1 | grep "prefix: fd02" | grep fd00 | wc -l

