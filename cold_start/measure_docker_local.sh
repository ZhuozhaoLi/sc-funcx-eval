#!/bin/bash

for i in `seq 1 1 100`
do
    time docker run funcx_py3.7_v0.1 python3 -c "import parsl; print(parsl.__version__, parsl.__file__)"
    # time shifter -- python3 -c "import parsl; print(parsl.__version__, parsl.__file__)"
done
