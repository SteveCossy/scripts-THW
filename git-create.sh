#!/bin/bash

# Script to automate the deployment of new private gitlab repos
# TODO: simplify and enhance error handling (already existing repos etc.)
#       expand script to handle: public repos, deletion, re-naming
# from: https://coderwall.com/p/r7yh6g/create-a-new-gitlab-repo-from-the-command-line#:~:text=saccy-,%23!/bin/bash,-%23%20Script%20to%20automate

token="your_token_here"

function usage {
  echo "Usage: $0 -n name"
  exit 1
}

number_args=$#
if [[ !("$number_args" -eq 2) ]]; then
  echo "Incorrect number of args" >&2
  echo "If two strings in name, quote them: e.g. \"str1 str2\""
  usage
fi

while getopts "n:" name; do
  case "${name}" in
    n)
      repo=${OPTARG}
      ;;
    \?)
      usage
      ;;
    *)
      usage
      ;;
  esac
done

if [[ -z ${repo} ]]; then
  echo "Option -n requires an argument." >&2
  usage
else
  echo "####### Creating new repo: ${repo} #######"
fi

# In case space separate words are used for the repo name, the first word will be used
# when naming the json output file.
repo_short=$(echo ${repo} | cut -d " " -f1)

response=$(curl -s -o ./temp.json -w '%{http_code}' \
-H "Content-Type:application/json" https://gitlab.ecs.vuw.ac.nz/api/v4/projects?private_token=$token \
-d "{ \"name\": \"${repo}\" }")
# ECS url added above, replacing gitlab.com

# Format JSON log
cat ./temp.json | python -m json.tool > ./${repo_short}_repo.json
rm -f ./temp.json

echo "Any JSON output is logged in ./${repo_short}_repo.json"
if [ $response != 201 ]; then
  echo Error
  echo "Response code: $response"
  exit 1
else
  echo "Repo successfully created"
  echo "Response code: $response"
  exit 0
fi
