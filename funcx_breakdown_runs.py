import json
import sys
import statistics
from funcx_sdk.client import FuncXClient

from scipy import stats

fxc = FuncXClient()


payload = [1,2,3]

import time
N = 100


# Cold start
ta = time.time()
cold_res = fxc.run(payload, "ip-172-31-6-144", "add_func")
tb = time.time()

print("Cold mean: {}".format(tb-ta))

warm_times = []

# PRIMER
for i in range(1,N):
    
    time.sleep(.05)
    t0 = time.time()
    res = fxc.run(payload, "ip-172-31-6-155", "add_func")
    t1 = time.time()
    print(t1-t0)
    warm_times.append(t1-t0)
    print(res)

print("MEAN: {}".format(statistics.mean(warm_times)))
print("STDEV: {}".format(statistics.stdev(warm_times)))

print(stats.describe(warm_times))

# res = fxc.run(payload, "ryan-laptop", "add_func")
# print(res)
