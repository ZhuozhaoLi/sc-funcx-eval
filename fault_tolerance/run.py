#!/usr/bin/env python3


import argparse
import time

import parsl
from parsl.app.app import python_app  # , bash_app

from parsl.providers import LocalProvider
from parsl.channels import LocalChannel
from parsl.launchers import SingleNodeLauncher
from parsl.addresses import *
import gc

from parsl.config import Config
from parsl.executors import HighThroughputExecutor

n_managers = 2
config = Config(
    executors=[
        HighThroughputExecutor(
            address=address_by_interface('bond0.144'),
            poll_period=1,
            heartbeat_period=1,
            heartbeat_threshold=2,
            label="htex_local",
            worker_mode="no_container",
            worker_ports=(53531, 53532),
            # worker_debug=True,
            cores_per_worker=1,
            max_workers=4,
            provider=LocalProvider(
                channel=LocalChannel(),
                init_blocks=0,
                max_blocks=1,
                # tasks_per_node=1,  # For HighThroughputExecutor, this option should in most cases be 1
                launcher=SingleNodeLauncher(),
            ),
        )
    ],
    retries=2,
    strategy=None,
)


@python_app
def sleeping_hello(dur, sim_fail=False):
    import time
    import os
    time.sleep(dur)
    if sim_fail:
        raise Exception("Simulated App Failure")
    return os.getpid(), dur

@python_app
def noop():
    pass

def run_test(n_tasks=8, sleep_dur=4, executor=None):

    futures = [sleeping_hello(sleep_dur) for i in range(n_tasks)]
    # futures = [noop() for i in range(n_tasks)]
    time.sleep(sleep_dur / 2)

    start = time.time()
    executor.scale_in(1)
    executor.scale_out(1)
    delta = time.time() - start
    print("Cost of start/stop : {}".format(delta))

    print([fu.result() for fu in futures])

    return

def wait_for_managers(executor, n_managers):
    attempt = 0
    while True:

        connected_managers = len(executor.connected_workers)
        if connected_managers < n_managers:
            print('attempt {}: waiting for {} managers, but only found {}'.format(attempt, n_managers,
                                                                                  connected_managers))
            time.sleep(2)
            attempt += 1
        else:
            print("All managers reporting")
            break

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sleep", default="4")
    parser.add_argument("-c", "--count", default="8",
                        help="Count of apps to launch")
    parser.add_argument("-d", "--debug", action='store_true',
                        help="Count of apps to launch")

    args = parser.parse_args()

    if args.debug:
        parsl.set_stream_logger()

    dfk = parsl.load(config)
    executor = dfk.executors["htex_local"]

    # We wait here to ensure that all managers have connected for a fair distribution of tasks
    wait_for_managers(executor, n_managers)
    run_test(int(args.count), int(args.sleep), executor)
