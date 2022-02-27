#!/bin/bash
set -eu

apt-get update && apt-get install libsasl2-dev libldap2-dev -y
poetry config virtualenvs.in-project true
poetry run pip install -U pip wheel
poetry install