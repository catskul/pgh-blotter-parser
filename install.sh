#!/bin/bash

script_path="$(readlink -f ./pull_and_parse.py)"
echo "0 5 * * 1 $script_path 2>> pull_and_parse.log" > cronentry


timestamp="$(date +'%Y-%m-%d_%H.%M.%S')"
crontab -l > "crontab.${timestamp}"
crontab cronentry
