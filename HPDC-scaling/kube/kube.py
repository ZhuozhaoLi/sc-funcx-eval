import subprocess
import sqlite3
import time

def grep_num_pods(pattens=['zhuozhao', 'ryan']):
    cmd = "kubectl get pods -n dlhub-privileged --no-headers=true | awk '/{}/ && !/Terminating/' | wc -l;"
    # cmd = ["kubectl", "get", "pods", "-n", "dlhub-privileged", "--no-headers=true", "|", "awk", "'/{}/ && /Running/'", "|", "wc"," -l"]
    cmds = ''
    for p in pattens:
        cmds += cmd.format(p)
    output = subprocess.check_output(cmds, shell=True)
    res = output.decode('ascii').strip("\n").split("\n")
    res = [int(r) for r in res]
    return res

def run(kill_event, patterns=['zhuozhao','ryan', 'logan']):
    #patterns = ['zz-funcx-kube-10-10', 'zz-funcx-kube-20-20', 'zz-funcx-kube-40-40']
    db = sqlite3.connect('data.db')
    db.execute("""create table if not exists pods(
        timestamp float,
        noop_0 int,
        noop_1 int,
        noop_10 int)"""
    )
    print("Database initiated")
    while not kill_event.is_set():
        res = grep_num_pods(patterns)
        result_data = (time.time(), res[0], res[1], res[2])
        print('inserting {}'.format(str(result_data)))
        db.execute("""
            insert into
            pods (timestamp, noop_0, noop_1, noop_10)
            values (?, ?, ?, ?)""", result_data
        )
        db.commit()
        #time.sleep(1)

if __name__ == '__main__':
    #print(grep_num_pods())
    import threading
    kill_event = threading.Event()
    run(kill_event)
