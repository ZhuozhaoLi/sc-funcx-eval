#!/bin/bash


# target_workers=32768
#for i in `seq 1 1`;
# Done 256 512 1024 64 128 256
for i in 64 128 256;
do
    target_workers=$i
    echo "Running htex with $target_workers"
    python run.py -i $target_workers -a $target_workers --queue debug
    #target_workers=$((target_workers*2))
    sleep 60
done

