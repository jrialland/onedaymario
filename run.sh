#!/bin/bash
set -euo pipefail
thisfile=$(readlink -m "$0")
thisdir=$(dirname "$thisfile")
set +u
source ./bin/activate
set -u
pip install -r requirements.txt
python -m onedaymario
