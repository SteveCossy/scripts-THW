for FILE in /local/scratch/stevecos/logs/*
   do
   echo -n "$FILE: "
   for OF in OF0 MRHOF
      do for DAG in 0 2
         do declare $OF$DAG=`grep "compare fd0$DAG::209:9:9:9 and fd0$DAG::209" $FILE | grep -c $OF`
      done
   done
     for OFi in OF0 MRHOF
      do for DAGi in 0 2
         do 
         declare NBR=$OFi$DAGi
         echo -n "$OFi+fd0$DAGi = ${!NBR}, "
      done
   done
   echo
done
