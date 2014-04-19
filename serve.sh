#!/bin/bash
kill $(fuser -a serve.log | cut -d ':' -f 2) &> /dev/null
cd json && (nohup python -m SimpleHTTPServer &>> ../serve.log &)
