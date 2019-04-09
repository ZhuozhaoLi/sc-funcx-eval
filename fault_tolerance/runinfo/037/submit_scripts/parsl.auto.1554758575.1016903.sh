
export CORES=$(getconf _NPROCESSORS_ONLN)
echo "Found cores : $CORES"
WORKERCOUNT=1

CMD ( ) {
process_worker_pool.py  --max_workers=4 -c 1 --poll 1 --task_url=tcp://127.0.0.1:54258 --result_url=tcp://127.0.0.1:54322 --logdir=/home/yadu/src/sc-funcx-eval/fault_tolerance/runinfo/037/htex_local --hb_period=1 --hb_threshold=2 
}
for COUNT in $(seq 1 1 $WORKERCOUNT)
do
    echo "Launching worker: $COUNT"
    CMD &
done
wait
echo "All workers done"
