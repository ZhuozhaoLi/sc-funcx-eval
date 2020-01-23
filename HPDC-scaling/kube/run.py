import argparse
from funcx.serialize import FuncXSerializer
# from funcx.queues import RedisQueue
from forwarder.queues import RedisQueue
import time
import sqlite3
import subprocess
from utils import sleep, template
from kube import run
import uuid
import threading

parser = argparse.ArgumentParser()
parser.add_argument("-r", "--redis_hostname", type=str, default='127.0.0.1',
                    help="Hostname of the Redis server")
parser.add_argument("-e", "--endpoint_id", type=str,
                    default="1197d583-5a8d-41eb-ba21-3c963e70fc6c",
                    help="Endpoint_id")
parser.add_argument("-y", "--endpoint_name", type=str,
                    default="funcx-kube",
                    help="Endpoint_name")
parser.add_argument("-t", "--tasks", type=int, default=20,
                    help="Number of tasks")
parser.add_argument("-i", "--num_workers", default=64,
                    type=int, help="maximum workers")
parser.add_argument("-a", "--workers_per_node",
                    type=int, default=64, help="number of workers per node")
parser.add_argument("-w", "--walltime",
                    type=str, default='00:60:00', help="walltime")
parser.add_argument("-c", "--container_type",
                    type=str, default='noop', help="container_type")
parser.add_argument("-n", "--trials", type=int,
                    default=1, help="number of trials per batch submission")
args = parser.parse_args()

# Initiate the result database
db = sqlite3.connect('data.db')
db.execute("""create table if not exists tasks(
    platform text,
    start_submit float,
    returned float,
    num_workers int,
    tasks_per_trial int,
    task_type text,
    failed int)"""
)
print("Database initiated")



# Create the config for the endpoint
config = template
#config = template.format(nodes=nodes,
#                         max_workers_per_node=max_workers_per_node,
#                         walltime=args.walltime)

endpoint_name = args.endpoint_name
with open("/home/zzli/.funcx/{}/config.py".format(endpoint_name), 'w') as f:
    f.write(config)

# Start the endpoint
cmd = "funcx-endpoint start {}".format(endpoint_name)
try:
    subprocess.call(cmd, shell=True)
except Exception as e:
    print(e)
print("Started the endpoint {}".format(endpoint_name))
print("Wating 10 seconds for the endpoint to start")
time.sleep(10)

# Connect to the task and result redis queue
endpoint_id = args.endpoint_id
tasks_rq = RedisQueue(f'task_{endpoint_id}', args.redis_hostname)
results_rq = RedisQueue(f'results', args.redis_hostname)
tasks_rq.connect()
results_rq.connect()
print("Redis queue connected")

# Create an instance of funcx serializer and serialize the function
fxs = FuncXSerializer()
ser_code = fxs.serialize(sleep)
fn_code = fxs.pack_buffers([ser_code])
print("Code serialized")

# Define the test function
def test(tasks=10, durs=[5, 10, 20], timeout=None):
    # Make sure there is no previous result left
    while True:
        try:
            x = results_rq.get(timeout=1)
        except:
            print("No more results left")
            break
    start_submit = time.time()
    time_table = {}
    rounds = 3
    #counts = [[1, 5, 20], [5, 20, 1], [20, 1, 5]]
    counts = [1, 5, 20]
    for k in range(rounds):
        for j, dur in enumerate(durs):
            tmp = str(uuid.uuid4())[:8]
            tasks = counts[j]
            for i in range(tasks):
                ser_args = fxs.serialize([dur])
                ser_kwargs = fxs.serialize({})
                input_data = fxs.pack_buffers([ser_args, ser_kwargs])
                payload = fn_code + input_data
                # container_id = "odd" if i%2 else "even"
                container_id = "zz-funcx-kube-{}-{}".format(dur, dur)
                container_address = '039706667969.dkr.ecr.us-east-1.amazonaws.com/f0f2bca0-23e3-436e-af9c-50875acbf0c7'
                task_id = tmp + str(i)
                time_table[task_id] = [dur, time.time()]
                tasks_rq.put(f"{task_id};{container_id},{container_address}", 'task', payload)
        end_submit = time.time()
        print("Launched {} tasks in {}".format(tasks*len(durs), end_submit - start_submit))
        if timeout:
            time.sleep(120)

    for i in range(sum(counts) * 3):
        if timeout:
            res = results_rq.get('result', timeout=timeout)
        else:
            res = results_rq.get('result', timeout=None)
        task_id = res[0]
        end = res[1]['completion_t']
        time_table[task_id].append(end)

    print("Printing result once for validation")
    print("Result : ", res)
    try:
        failed = False
        print("Result : ", fxs.deserialize(res[1]['result']))
    except:
        failed = True
        print("Result : ", fxs.deserialize(res[1]['exception']))

    return time_table, failed


durs = [1, 10, 20]
patterns = ['zz-funcx-kube-{}-{}'.format(dur, dur) for dur in durs]
# Priming the endpoint with tasks
print("\nAll initialization done. Start priming the endpoint")
#test()

# Testing -- repeat for `trials` times
print("\nStart testing")
kill_event = threading.Event()
kube_thread = threading.Thread(target=run, args=(kill_event, patterns))
kube_thread.daemon = True
kube_thread.start()
for trial in range(args.trials):
    print("Testing trial {}/{}".format(trial+1, args.trials))
    try:
        time_table, failed = test(tasks=args.tasks, durs=durs, timeout=300)
        print(time_table)
        # Recording results to db
        for k in time_table:
            dur, start, end = time_table[k]
            result_data = ('kube', start, end, 
                    args.num_workers, args.tasks, 'sleep-{}'.format(dur), failed)
            print('inserting {}'.format(str(result_data)))
            db.execute("""
                insert into
                tasks (platform, start_submit, returned, num_workers, tasks_per_trial, task_type, failed)
                values (?, ?, ?, ?, ?, ?, ?)""", result_data
            )
            db.commit()
    except Exception as e:
        print(e)
time.sleep(10)
kill_event.set()

# Stop the endpoint
cmd = "funcx-endpoint stop {}".format(endpoint_name)
try:
    # stop twice to make sure
    subprocess.call(cmd, shell=True)
    subprocess.call(cmd, shell=True)
except Exception as e:
    print(e)
print("\nStopped the endpoint {}".format(args.endpoint_id))
print("Wating 180 seconds for the endpoint to stop")
time.sleep(10)

