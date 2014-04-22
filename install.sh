#!/bin/bash

virtualenv ./env
. ./env/bin/activate
pip install --pre -r requirements.txt

script_path="$(readlink -f ./pull_and_parse.py)"
echo "0 5 * * 1 $(pwd)/env/bin/python $script_path 2>> $(pwd)/pull_and_parse.log" > cronentry


timestamp="$(date +'%Y-%m-%d_%H.%M.%S')"
crontab -l > "crontab.${timestamp}"
crontab cronentry
