#!/bin/sh
WORK_PATH="${PWD}"
export PYTHONPATH=${WORK_PATH}:${PYTHONPATH}
python ./app/auth.py
