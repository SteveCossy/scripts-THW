for FILE in /home/stevecos/Cooja/10-RPL-202509*
   do for OF in OF0 MRHOF
      do for DAG in 0 2
         do declare $OF$DAG=`grep "compare fd0$DAG::209:9:9:9 and fd0$DAG::209" $FILE | grep -c $OF`
      done
   done
   for OFi in OF0 MRHOF
      do for DAGi in 0 2
         declare NBR=$OF$DAG
         do echo -n "${!NBR},"
      done
   done
   echo
done
