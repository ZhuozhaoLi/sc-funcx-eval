import argparse
import math
import os
import time
import sqlite3
import subprocess
import sys
import glob

import parsl
from parsl.config import Config
from parsl.executors import HighThroughputExecutor
from parsl.providers import LocalProvider
from parsl.channels import LocalChannel
from parsl.providers import SlurmProvider
from parsl.launchers import SrunLauncher

# from parsl.launchers import SimpleLauncher
from parsl.launchers import SingleNodeLauncher
from parsl.addresses import address_by_interface

from parsl.config import Config
from parsl.executors import HighThroughputExecutor
import os

from parsl.app.app import python_app, bash_app
from parsl.launchers import SimpleLauncher
from parsl.launchers import SingleNodeLauncher
from parsl.addresses import address_by_hostname
from parsl.launchers import AprunLauncher
from parsl.providers import TorqueProvider

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--min_workers", type=int, default=32, help="minimum workers")
parser.add_argument("-a", "--max_workers", type=int, default=32, help="maximum workers")
parser.add_argument("-r", "--trials", type=int, default=1, help="number of trials per batch submission")
parser.add_argument("-t", "--tasks_per_trial", type=int, default=100000, help="number of tasks per trial")
parser.add_argument("-c", "--cores_per_node", type=int, default=256, help="cores per node")
parser.add_argument("-w", "--walltime", type=str, default='05:40:00', help="walltime")
parser.add_argument("-q", "--queue", type=str, default='normal', help="queue")
args = parser.parse_args()

# parsl.set_stream_logger()

db = sqlite3.connect('data.db')
db.execute("""create table if not exists tasks(
    executor text,
    start_submit float,
    end_submit float,
    returned float,
    connected_workers int,
    tasks_per_trial,
    tag text)"""
)


def raw_sleep1000ms():
    try:
        import os
    except Exception:
        return -1
    
    try:
        os.system("sleep 1")
    except Exception:
        return -2
    return 0

target_workers = args.min_workers
while target_workers <= args.max_workers:
    #subprocess.call("qstat -u $USER | awk '{print $1}' | grep -o [0-9]* | xargs qdel", shell=True)
    
    needed_time = args.tasks_per_trial * args.trials * 2 / target_workers 
    if needed_time <= 1800: needed_time = 1800
    walltime = time.strftime('%H:%M:%S', time.gmtime(needed_time))
    print("The walltime for {} workers is {}".format(target_workers, walltime))
    
    if target_workers % args.cores_per_node != 0:
        nodes_per_block = 1
        tasks_per_node = target_workers % args.cores_per_node 
    else:
        nodes_per_block = int(target_workers / args.cores_per_node)
        tasks_per_node = args.cores_per_node 

    config = Config(
        executors=[
            HighThroughputExecutor(
                label="cori_funcX_shifter",
                address=address_by_interface('bond0.144'),
                worker_debug=True,
                # worker_mode="singularity_reuse",
                worker_mode="shifter_reuse",
                # worker_mode="singularity_single_use",
                # worker_mode="no_container",
                # We always want the container to be in the home dir.
                container_image="yadudoc/funcx_py3.7_v0.1:latest", # os.path.expanduser("~/sing-run.simg"),
                cores_per_worker=1,
                #max_workers=8,
                max_workers=tasks_per_node,
                provider=SlurmProvider(
                    partition=args.queue,  # Replace with partition name
                    init_blocks=1,
                    min_blocks=1,
                    max_blocks=1,
                    nodes_per_block=nodes_per_block,
                    walltime="00:30:00",
                    scheduler_options='''#SBATCH --constraint=knl,quad,cache
#SBATCH --image=yadudoc/funcx_py3.7_v0.1:latest
''',
                    #scheduler_options="#SBATCH --constraint=haswell",
                    worker_init='source ~/setup_funcx_py3.7.sh',
                    launcher=SrunLauncher(overrides='-c 64'),
                    cmd_timeout=120,
                ),
            )
        ],
        # run_dir="/home/ubuntu/parsl/parsl/tests/manual_tests/runinfo/",
        # run_dir="/global/homes/y/yadunand/funcX/parsl/tests/manual_tests/runinfo",
        run_dir="/global/homes/y/yadunand/HPDC19-code/parsl-htex/cori/strong-scaling/runinfo",
        strategy=None,
    )
    
    print(config)

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
    def sleep10s():
        import time
        time.sleep(10.0)

    @python_app
    def sleep100s():
        import time
        time.sleep(100.0)

    @bash_app
    def bash_sleep1s():
        return "sleep 1"

    attempt = 0
    #cmd = 'ls {} | wc -l'.format(os.path.join(executor.run_dir, executor.label, '*', '*worker*'))
    path = os.path.join(executor.run_dir, executor.label, '*', '*worker*')

    while True:
        #connected_workers = int(subprocess.check_output(cmd, shell=True))
        #connected_workers = len(glob.glob(path, recursive=True))
        connected_managers = len(executor.connected_workers)
        if connected_managers < nodes_per_block:
            print('attempt {}: waiting for {} managers, but only found {}'.format(attempt, nodes_per_block, connected_managers))
            time.sleep(30)
            attempt += 1
        else:
            tasks = [noop() for _ in range(0, target_workers)]
            [t.result() for t in tasks]
            dfk.tasks = {}
            break

    #for app in [noop]:
    #for app in [noop, sleep10ms, sleep100ms, sleep1000ms, sleep10s, sleep100s]:
    #for app in [noop, sleep10ms, sleep100ms, sleep1000ms, sleep10s]:
    for app in [bash_sleep1s]:
        sum1 = sum2 = 0
        #end_submit = 0
        for trial in range(args.trials):
            try:
                start_submit = time.time()
                tasks = [app() for _ in range(0, args.tasks_per_trial)]
                # tasks = [executor.submit(raw_sleep1000ms) for _ in range(0, args.tasks_per_trial)]
                end_submit = time.time()
                [t.result() for t in tasks]
                returned = time.time()

                data = (
                    executor.label,
                    start_submit,
                    end_submit,
                    returned,
                    target_workers,
                    args.tasks_per_trial,
                    app.__name__
                )
                print('inserting {}'.format(str(data)))
                db.execute("""
                    insert into
                    tasks(executor, start_submit, end_submit, returned, connected_workers, tasks_per_trial, tag)
                    values (?, ?, ?, ?, ?, ?, ?)""", data
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
        print("The average submitted time of {} is {}".format(app.__name__, sum1/args.trials))
        print("The average running time of {} is {}".format(app.__name__, sum2/args.trials))

    target_workers *= 2
    executor.shutdown()
    del dfk
