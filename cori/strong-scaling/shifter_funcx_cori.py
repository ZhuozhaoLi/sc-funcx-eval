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

config = Config(
    executors=[
        HighThroughputExecutor(
            # poll_period=10,
            label="htex_local",
            address=address_by_interface('bond0.144'),
            # worker_debug=True,
            # worker_mode="singularity_reuse",
            worker_mode="shifter_reuse",
            # worker_mode="singularity_single_use",
            # worker_mode="no_container",
            # We always want the container to be in the home dir.
            container_image="yadudoc/funcx_py3.7_v0.1:latest", # os.path.expanduser("~/sing-run.simg"),
            cores_per_worker=1,
            #max_workers=8,
            max_workers=64,
            provider=SlurmProvider(
                partition='debug',  # Replace with partition name
                init_blocks=1,
                min_blocks=1,
                scheduler_options='''#SBATCH --constraint=knl,quad,cache
#SBATCH --image=yadudoc/funcx_py3.7_v0.1:latest
''',
                #scheduler_options="#SBATCH --constraint=haswell",
                worker_init='source ~/setup_funcx_py3.7.sh',
                launcher=SrunLauncher(overrides='-c 64'),
            ),
        )
    ],
    # run_dir="/home/ubuntu/parsl/parsl/tests/manual_tests/runinfo/",
    run_dir="/global/homes/y/yadunand/funcX/parsl/tests/manual_tests/runinfo",
    strategy=None,
)
