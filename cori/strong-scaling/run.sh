#!/bin/bash

queue='debug'
#for i in `seq 1 2`;

# Pending 65536

# for i in 4096;
for i in 256;
do
    target_workers=$i
    echo "Running HTEX with $target_workers"
    python run.py -i $target_workers -a $target_workers -q $queue
    #target_workers=$((target_workers*2))
    sleep 60
done


