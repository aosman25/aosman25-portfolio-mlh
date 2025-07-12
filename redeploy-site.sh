#!/bin/bash

cd aosman25-portfolio-mlh && \
git fetch && git reset origin/main --hard > /dev/null/ && \
if [ ! -d python3-virtualvenv ]; then python3 -m venv python3-virtualvenv; fi && \
source ./python3-virtualvenv/bin/activate > /dev/null/ && \
pip install -r requirements.txt > /dev/null/ && \
systemctl restart myportfolio &&\
echo "Successfully Restarted myportfolio Serivce!"