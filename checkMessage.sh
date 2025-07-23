
fileName=/home/stevecos/message.txt
timestamp=`date +%Y.%m.%d-%H:%M`
if test -f $fileName ; then
	echo ECS Message $timestamp
	cat $fileName 
	mv $fileName $fileName-$timestamp
fi
