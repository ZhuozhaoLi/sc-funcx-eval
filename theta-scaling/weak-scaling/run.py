import argparse
import math
import os
import time
import sqlite3
import subprocess
import sys
import glob
import gc

import parsl
from parsl.config import Config
from parsl.executors import HighThroughputExecutor
from parsl.app.app import python_app
from parsl.launchers import SimpleLauncher
from parsl.launchers import SingleNodeLauncher
from parsl.addresses import address_by_hostname
from parsl.launchers import AprunLauncher
from parsl.providers import CobaltProvider

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--min_workers", type=int, default=64, help="minimum workers")
parser.add_argument("-a", "--max_workers", type=int, default=64, help="maximum workers")
parser.add_argument("-r", "--trials", type=int, default=1, help="number of trials per batch submission")
parser.add_argument("-t", "--tasks_per_worker", type=int, default=10, help="number of tasks per worker")
parser.add_argument("-c", "--cores_per_node", type=int, default=256, help="cores per node")
parser.add_argument("-u", "--cores_per_worker", type=int, default=4, help="cores per worker")
parser.add_argument("-w", "--walltime", type=str, default='05:40:00', help="walltime")
parser.add_argument("-q", "--queue", type=str, default='default', help="queue")
args = parser.parse_args()

# parsl.set_stream_logger()

db = sqlite3.connect('data.db')
db.execute("""create table if not exists tasks(
    executor text,
    start_submit float,
    end_submit float,
    returned float,
    num_nodes int,
    connected_workers int,
    tasks_per_trial,
    tag text)"""
)

target_workers = args.min_workers
while target_workers <= args.max_workers:
    #subprocess.call("qstat -u $USER | awk '{print $1}' | grep -o [0-9]* | xargs qdel", shell=True)
    
    needed_time = args.tasks_per_worker * args.trials * 2
    if needed_time <= 2400: needed_time = 2400
    walltime = time.strftime('%H:%M:%S', time.gmtime(needed_time))
    print("The walltime for {} workers is {}".format(target_workers, walltime))

    tasks_per_node = int(args.cores_per_node / args.cores_per_worker)
    if target_workers % tasks_per_node != 0:
        nodes_per_block = 1
        tasks_per_node = target_workers % tasks_per_node 
    else:
        nodes_per_block = int(target_workers / tasks_per_node)
        tasks_per_node = tasks_per_node 

    config = Config(
        executors=[
            HighThroughputExecutor(
                label="theta_funcx",
                #worker_debug=True,
                max_workers=tasks_per_node, # Experimental 
                #suppress_failure=True, # Experimental
                heartbeat_period=60,
                heartbeat_threshold=600,
                cores_per_worker=args.cores_per_worker,
                address=address_by_hostname(),
                #container_image=os.path.expanduser("~/sing-run.simg"),
                container_image='/tmp/sing-run.simg',
                worker_mode="singularity_reuse",
                #worker_mode="no_container",
                provider=CobaltProvider(
                    queue=args.queue,
                    #account='ExM',
                    account='CSC249ADCD01',
                    launcher=AprunLauncher(overrides="-d 64"),
                    scheduler_options='',
                    # worker_init='source ~/move_image.sh\nsource activate funcx-test'.format(os.getenv('PWD')),
                    worker_init='source activate funcx-test\naprun -n {} -N 1 /bin/bash ~/move_image.sh'.format(nodes_per_block),
                    init_blocks=1,
                    max_blocks=1,
                    min_blocks=1,
                    nodes_per_block=nodes_per_block,
                    walltime=walltime,
                    cmd_timeout=60
               ),                    
            )
        ],
        run_dir="{}/runinfo/".format(os.getenv('PWD')),
        strategy=None
    )
    #print(config)

    parsl.clear()
    dfk = parsl.load(config)
    executor = list(dfk.executors.values())[0]

    @python_app
    def noop():
        pass

    @python_app
    def sleep10ms():
        import time
        time.sleep(0.01)
        #sleep(0.01)

    @python_app
    def sleep100ms():
        import time
        time.sleep(0.1)
        #sleep(0.1)

    @python_app
    def sleep1000ms():
        import time
        time.sleep(1.0)
        #sleep(1.0)

    @python_app
    def sleep10s():
        import time
        time.sleep(10.0)

    @python_app
    def sleep100s():
        import time
        time.sleep(100.0)

    attempt = 0
    #cmd = 'ls {} | wc -l'.format(os.path.join(executor.run_dir, executor.label, '*', '*worker*'))
    path = os.path.join(executor.run_dir, executor.label, '*', '*worker*')

    while True:
        #connected_workers = int(subprocess.check_output(cmd, shell=True))
        #connected_workers = len(glob.glob(path, recursive=True))
        connected_managers = len(executor.connected_workers)
        if connected_managers < nodes_per_block * 0.92:
            print('attempt {}: waiting for {} managers, but only found {}'.format(attempt, nodes_per_block, connected_managers))
            time.sleep(60)
            attempt += 1
        else:
            #time.sleep(180)
            tasks = [noop() for _ in range(0, target_workers)]
            [t.result() for t in tasks]
            dfk.tasks = {}
            del tasks
            gc.collect()
            break

    #for app in [noop, sleep10ms, sleep100ms, sleep1000ms]:
    #for app in [noop, sleep10ms, sleep100ms, sleep1000ms, sleep10s, sleep100s]:
    #for app in [noop, sleep10ms, sleep100ms, sleep1000ms, sleep10s]:
    for app in [noop, sleep100ms, sleep1000ms]:
        sum1 = sum2 = 0
        print("The number of connected managers is {}".format(len(executor.connected_workers)))
        #end_submit = 0
        for trial in range(args.trials):
            try:
                start_submit = time.time()
                tasks = [app() for _ in range(0, args.tasks_per_worker * target_workers)]
                end_submit = time.time()
                [t.result() for t in tasks]
                returned = time.time()

                data = (
                    executor.label,
                    start_submit,
                    end_submit,
                    returned,
                    nodes_per_block,
                    target_workers,
                    args.tasks_per_worker * target_workers,
                    app.__name__
                )
                print('inserting {}'.format(str(data)))
                db.execute("""
                    insert into
                    tasks(executor, start_submit, end_submit, returned, num_nodes, connected_workers, tasks_per_trial, tag)
                    values (?, ?, ?, ?, ?, ?, ?, ?)""", data
                )
                db.commit()
                t1 = (end_submit - start_submit) * 1000
                t2 = (returned - start_submit) * 1000
                sum1 += t1
                sum2 += t2
                print("Submitted time is %.6f ms" % t1)
                print("Running time is %.6f ms\n" % t2)
            except Exception as e:
                print(e)
            dfk.tasks = {}
            del tasks
            gc.collect()
        print("The average submitted time of {} is {}".format(app.__name__, sum1/args.trials))
        print("The average running time of {} is {}".format(app.__name__, sum2/args.trials))
        print("The number of connected managers is {}".format(len(executor.connected_workers)))

    target_workers *= 2
    executor.shutdown()
    del dfk
