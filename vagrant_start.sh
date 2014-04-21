#!/bin/bash

# Disable CACHE to simplify coding
# export PYBOSSA_REDIS_CACHE_DISABLED='1'

. /opt/vagrant_env/bin/activate
python run.py
