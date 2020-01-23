import base64

def sleep(dur):
    import time
    time.sleep(dur)
    return 1

template = """
from funcx.config import Config
from funcx.providers import KubernetesProvider
from funcx.strategies import KubeSimpleStrategy

config = Config(
    scaling_enabled=True,
    worker_debug=True,
    provider=KubernetesProvider(
        namespace="dlhub-privileged",
        image='039706667969.dkr.ecr.us-east-1.amazonaws.com/f0f2bca0-23e3-436e-af9c-50875acbf0c7',
        worker_init="pip install parsl==0.9.0;pip install git+https://github.com/funcx-faas/funcX.git@zz_container_adv;export PYTHONPATH=$PYTHONPATH:/app",
        secret="ryan-kube-secret",
        pod_name='funcx-kube-test',
        nodes_per_block=1,
        init_blocks=0,
        max_blocks=10,
        #persistent_volumes=[('funcx', '/mnt')],
    ),
    working_dir='/app',
    heartbeat_period=2,
    heartbeat_threshold=6,
    max_workers_per_node=1,
    strategy=KubeSimpleStrategy(max_idletime=8),
)
""" 
