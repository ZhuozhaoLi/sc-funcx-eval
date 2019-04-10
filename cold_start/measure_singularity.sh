#!/bin/bash

for i in `seq 1 1 100`
do
    time singularity --image="ZZ_TO_FILL" -c "import parsl; print(parsl.__version__, parsl.__file__)" 
done
