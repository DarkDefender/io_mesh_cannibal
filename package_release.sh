#!/bin/bash

# Stop on errors
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
RELEASE_DIR=release/io_mesh_cannibal/

cd $SCRIPT_DIR

rm -fr release/*
mkdir -p $RELEASE_DIR
cp -r formats $RELEASE_DIR
cp cpj_utils.py export_cpj.py import_cpj.py __init__.py kaitaistruct.py $RELEASE_DIR

cd release
zip -r io_mesh_cannibal_addon.zip io_mesh_cannibal -x "*/__pycache__/*"
