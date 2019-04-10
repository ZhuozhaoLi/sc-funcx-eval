#!/bin/bash

x="shifter_measures.txt"
for i in `seq 1 1 100`
do
    time shifter -- python3 -c "import parsl; print(parsl.__version__, parsl.__file__)" &> x
done
