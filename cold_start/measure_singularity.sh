#!/bin/bash

for i in `seq 1 1 100`
do
    time singularity exec /home/zzli/sing-run.simg python3 -c "import parsl; print(parsl.__version__, parsl.__file__)" 
done
