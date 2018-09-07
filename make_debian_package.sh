#!/usr/bin/env bash

cp requirements.txt requirements.txt.ori

mkdir build_dependencies
pip3 wheel -r requirements.txt --wheel-dir build_dependencies

rm requirements.txt
for dep in build_dependencies/*; do echo "${dep}" >> requirements.txt ; done 

find build_dependencies/ -name '*~' -delete
find build_dependencies/ -name '*.pyc' -delete
find build_dependencies/ -name '__pycache__' -delete

debuild
debuild clean

mv requirements.txt.ori requirements.txt 
rm -rf build_dependencies build dist pyfuse.egg-info
mkdir -p debuild
mv ../pyfuse_*.* debuild/.
