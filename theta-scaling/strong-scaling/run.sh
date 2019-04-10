#!/bin/bash


target_workers=64
queue='default'
#queue='debug-flat-quad'
#for i in `seq 1 2`;
#for i in 64 128 256 512;
for i in 65536;
#for i in 32768;
#for i in 64;
do
    target_workers=$i
    echo "Running HTEX with $target_workers"
    python run.py -i $target_workers -a $target_workers -q $queue
    #target_workers=$((target_workers*2))
    sleep 180
done

