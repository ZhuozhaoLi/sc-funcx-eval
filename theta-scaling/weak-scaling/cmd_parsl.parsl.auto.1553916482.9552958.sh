process_worker_pool.py  --max_workers=64 -c 4 --poll 10 --task_url=tcp://thetalogin2:54051 --result_url=tcp://thetalogin2:54140 --logdir=/home/zzli/funcx-testing-code/funcx/theta/weak-scaling/runinfo/020/theta_funcx --hb_period=30 --hb_threshold=240 --mode=singularity_reuse --container_image=/tmp/sing-run.simg 
