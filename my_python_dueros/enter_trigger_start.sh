#!/bin/sh

WORK_PATH="${PWD}"
export PYTHONPATH=${WORK_PATH}:${PYTHONPATH}

python ./app/enter_trigger_main.py