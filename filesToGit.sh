# Send a specified folder of files to GitHub
# Steve Cosgrove updated 20 March 2024

logFileName=/home/stevecos/filesToGit/filesToGit_`date +%F`
# changed 2 Dec logFileName=/home/stevecos/Documents/MastersProposal/gitLogs/filesToGit_`date +%F`
# logFileName=/home/stevecos/scripts/scriptLogs/filesToGit_`date +%F`
# Doesn't help because it is outside the git path

gitCommitName=THW-`date +%F_%T`

randomOneSearch=/home/stevecos/Documents/MastersProposal/

echo `date` >>$logFileName

for DIR in $@
do
   echo $DIR >>$logFileName
   cd $DIR
   /usr/pkg/bin/git pull >>$logFileName 2>/dev/null
   /usr/pkg/bin/git add .
   if [[ $randomOneSearch -ef $DIR ]]
   then
      /usr/pkg/bin/git add /home/stevecos/Documents/MastersProposal/gitLogs/filesToGit*
   fi
   echo \*\*\*\* >>$logFileName
   /usr/pkg/bin/git commit -m "$gitCommitName" >>$logFileName 2>/dev/null
   /usr/pkg/bin/git push >>$logFileName 2>/dev/null
done

