# Checking contents of log files

FUNCTION="dao_input_nonstoring()"
SEARCH="Sending a DAO with"
TEST1a="fd00"
TEST1b="fd02"
TEST2a="fd00"
TEST2b="fd02"

#FUNCTION="dao_input_nonstoring()"
#SEARCH="DAO lifetime:"
#TEST1a="prefix: fd00"
#TEST1b="prefix: fd02"
#TEST2a="fd00"
#TEST2b="fd02"

echo Parsing output from $FUNCTION
echo -n "$SEARCH with $TEST1a lines: "
grep -n "$SEARCH" $1 | grep "$TEST1a" |  wc -l 
echo -n "$SEARCH with $TEST1b lines: "
grep -n "$SEARCH" $1 | grep "$TEST1b" |  wc -l
echo -n "$SEARCH with $TEST1a & not $TEST2a lines: "
grep -n "$SEARCH" $1 | grep "$TEST1a" | grep $TEST2b | wc -l
echo -n "$SEARCH with $TEST1b & not $TEST2a lines: "
grep -n "$SEARCH" $1 | grep "$TEST1b" | grep $TEST2a | wc -l

