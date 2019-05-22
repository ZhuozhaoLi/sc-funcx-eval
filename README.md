# SC AD/AE Document


This repository contains the codes and configurations used to perform each of the experiments included in the SC funcX paper.

Here we describe how the experiments were configured, where their respective scripts are, and provide the raw data and code to generate the plots presented in the paper.

## Table of contents

1. [Setup](#setup)
2. [Latency experiment](#latency)
3. [Cold starts](#cold starts)
4. [Container instantiation](#container instantiation)
5. [Scalability](#scalability)
6. [Fault tolerance](#fault tolerance)
7. [Batching](#batching)
8. [Prefetching](#prefetching)
9. [Memoization](#memoization)

## Setup

To execute funcX functions you must first deploy a funcX endpoint. We provide a public github repository (ANONYMIZED) and documentation (ANONYMIZED) to guide users through deploying an endpoint and registering functions. A brief summary of these instructions are provided here:

1. Clone the funcx-endpoint repository: 

`$ git clone https://github.com/funcx-faas/funcx-endpoint`

2. Install the endpoint: 

`$ cd funcx-endpoint; python setup.py install`

3. Start the endpoint: 

`$ funcx_endpoint`

4. Authenticate with a valid globus Identity Provider

Your endpoint will now be registered with the funcX service and will periodically receive heartbeat messages. It can also now be used to invoke functions. An example of defining, publishing, and using funcX functions is also provided in the associated documentation. Here we provide a brief overview of these examples.

1. Clone the funcx-sdk repository: 

`$ git clone https://github.com/funcx-faas/funcx-sdk`

2. Install the sdk: 

`$ cd funcx_sdk; python setup.py install`

3. Open a python terminate and import the funcX client: 

`$ python3`
`>>> from funcx_sdk.client import FuncXClient`

4. Instantiate the client:

`>>> fxc = FuncXClient()`

5. Follow the login prompt.

6. Define a test function:

`>>> func = """`
`def test_add(event):`
`    nums = event["data"]`
`    sum_val = sum(nums)`
`    return sum_val`
`"""`

7. Publish the function to the service:

`>>> fxc.register_function("test_add", func, "test_add", description="A test function.")`

8. Run the function:

`>>> payload = [1,2,3,11]`
`>>> res = fxc.run(payload, "user#laptop", "add_func")`
`>>> print(res)`


## Latency

We performed latency tests by deploying a hello-world function on: AWS Lamda, Google Functions, Azure Functions, and funcX. We selected US East regions to host the functions and deployed funcX on a US East EC2 instance. We then deployed a script on ANL's Cooley cluster to invoke each of these functions 2000 times and recorded the results. The script "primes" each function by calling it once to ensure it was warm for subsequent tests. The script used to perform this experiment is available under the latency directory of the associated repository.

## Cold Starts

To evaluate the performance of "cold" containers (where they are not cached by the provider) we modified the above latency script with a >10 minute delay (Google's cache is 10 minutes). We then polled the functions once without priming. To evaluate funcX, we terminated the service and restarted it, forcing it to deploy new containers. Each of these experiments can be recreated by running the scripts located in the cold start directory of the repository.


## Container Instantiation
We use the respective cold\_start scripts (cori, theta, ec2) to repeatedly create a container, load Python and Parsl, then print the parsl.__version__. We deployed this script on each of the selected resources (Cori, Theta, EC2) and used the respective containers. The result of these experiments are also available within the repository’s data directory.

## Scalability

We deployed funcX on Cori and Theta and configured it to acquire different numbers of resources to perform each test. Our testing tool (available in the associated github repository’s /experiments/scalability directory) would wait for all of the workers to connect back to the endpoint before initiating the tests. Tests were performed by dispatching sleep (1 second) and noop (return without doing anything) tasks.

## Fault Tolerance

We used a similar configuration to the scaling tests to evaluate the fault tolerance of funcX. We configured an endpoint to deploy two workers locally. Once connected, we started dispatching 100ms sleep tasks to the workers until they were saturated with tasks. We then terminated a worker while maintaining the task submission rate. The endpoint then detects the worker's failure via a 2 second heartbeat and replaces the worker. We ran the test for 10 seconds. The scripts used to perform these tests are available in the fault\_tolerance directory of the repository.

## Batching

For each of the scientific use cases we configured an endpoint to provision one worker. We then submitted jobs with increasing numbers of functions to perform (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024) and measured how long the job took to complete. Our scripts are available in the repository. Each of the experimental scripts and their resulting databases are available in the batching directory of the repository.

## Prefetching


## Memoization

To explore the memoization optimization we conduct an experiment using XXX mnist inputs. We evaluate the effect of memoization by varying the number of duplicate requests, using 0%, 25%, 50%, and 100% duplicate requests. Prior to running the test we prime the experiment with the duplicates such that they are stored in the cache.


