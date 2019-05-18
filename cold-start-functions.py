import boto3
import time
import statistics
import requests
import sqlite3


N = 2

db_file = "cold_starts.db"

# conn = create_connection(db_file)

try:
    conn = sqlite3.connect(db_file)
except Error as e:
    print(e)



def lambda_test(num_runs):
    
    client = boto3.client('lambda')

    #print("Priming...")
    #invoke_response = client.invoke(
    #    FunctionName="tylerfunc2",
    #    InvocationType="RequestResponse"
    #)

    #print("Priming complete! Running now...")

    times = []
    for i in range(1, num_runs):

        # time.sleep(.5)
        time0 = time.time()

        invoke_response = client.invoke(
            FunctionName="tylerfunc2",
            InvocationType="RequestResponse"
        )

        # print(invoke_response['Payload'].read())
        # print(res)
        time1 = time.time()

        times.append(time1-time0)
        insert_data(time1-time0, 'lambda')
        #time.sleep(600)

    return times



# def hello_get(request):
#     """HTTP Cloud Function.
#     Args:
#         request (flask.Request): The request object.
#         <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
#     Returns:
#         The response text, or any set of values that can be turned into a
#         Response object using `make_response`
#         <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
#     """
#     return 'Hello World!'

def google_test(num_runs):
    # curl -X POST "https://us-central1-noble-cubist-236315.cloudfunctions.net/function-1" -H "Content-Type:application/json" --data '{"name":"Keyboard Cat"}'


    #print("Priming...")
    data = {"name":"Keyboard Cat"}
    #r = requests.post("https://us-east1-noble-cubist-236315.cloudfunctions.net/function-2", data=data)

    # r = requests.post("https://us-central1-noble-cubist-236315.cloudfunctions.net/function-1", data=data)
    #print(r.text)
    #print("Priming completed! Running now! ")

    times = []
    for i in range(1, num_runs):
        # time.sleep(.5)
        time0 = time.time()

        r = requests.post("https://us-east1-noble-cubist-236315.cloudfunctions.net/function-2", data=data)

        # r = requests.post("https://us-central1-noble-cubist-236315.cloudfunctions.net/function-1", data=data)
        # print(r.text)
        time1 = time.time()

        times.append(time1 - time0)
        insert_data(time1-time0, 'google')
        #time.sleep(600)

    return times

def azure_test(num_runs):


    #print("Priming...")
    #url = "https://tylerfuncxapp1.azurewebsites.net/api/HttpTrigger?code=6AAItaCsm2wPwGxqnqnYbD3MnOM8wF2i1QK1Y31gMkbAGF6XLLaU5Q=="
    #payload = {'name': 'world'}
    #x = requests.post(url, json=payload)
    #print(x.text)

    times = []
    for i in range(1, num_runs):
        # time.sleep(.5)
        time0 = time.time()

        url = "https://tylerfuncxapp1.azurewebsites.net/api/HttpTrigger?code=6AAItaCsm2wPwGxqnqnYbD3MnOM8wF2i1QK1Y31gMkbAGF6XLLaU5Q=="
        payload = {'name': 'world'}
        x = requests.post(url, json=payload)
        # print(x.text)

        time1 = time.time()

        times.append(time1 - time0)
        insert_data(time1-time0, 'azure')
        #time.sleep(600)
    return times


def funcx_test(num_runs):

    #print("Priming...")
    # url = ""
    # payload = {'name': 'world'}
    # x = requests.post(url, json=payload)
    # print(x.text)

    times = []
    for i in range(1, num_runs):
        # time.sleep(.5)
        time0 = time.time()

        url = "http://ec2-100-25-77-39.compute-1.amazonaws.com:8080/runjob"
        payload = {'cmd': 'echo hello world'}
        x = requests.get(url, json=payload)
        # print(x.text)

        time1 = time.time()

        times.append(time1 - time0)
        print("INSERTING DATA") 
        insert_data(time1-time0, 'funcx')

    return times


def insert_data(tot_time, job_type):
    sql = """INSERT INTO tasks(tot_time, job_type) VALUES({},'{}');""".format(tot_time, "cold-" + job_type)
    print(sql)

    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()    
    return None

if __name__ == "__main__":
    while True:
        # AWS Lambda
        #print("Running AWS Lambda Tests... \n")
        lambda_times = lambda_test(N)
        #print(lambda_times)
        #print(statistics.mean(lambda_times))

        # Google Cloud Functions
        #print("Running Google Cloud Function Tests... \n")

        google_times = google_test(N)
        #print(google_times)
        #print(statistics.mean(google_times))
        #print(statistics.mean(google_times))

        # MS Azure Functions
        #print("Running Microsoft Azure Function Tests... \n")
        azure_times = azure_test(N)
        #print(azure_times)
        #print(statistics.mean(azure_times))

        # FuncX Functions 
        #print("Running FuncX Tests \n")
        funcx_times = funcx_test(N)
        #print(funcx_times)
        #print(statistics.mean(funcx_times))
        print("Sleeping for 10 minutes (and 1 second)!")
        time.sleep(601)
