# Sample Boto3 AWS Resource inspection scriptions

**DISCLAIMER:** These scripts are samples to help you explore how AWS Boto3 can help you inspect your resource inventories.  These scripts are not guaranteed nor supported in any way.  Use only after you have received some training in B0to3.

## Project Tenants
1. Running the evaluator scripts needs to be SIMPLE
2. The results from the evaluator scripts needs to be actionable and easy to understand for an infrastructure / system engineer.
3. The results will feed into the WAR document for each workload.  Workloads are identified by a product specific tag.  If the customer has not completed product/application/service tagging, then only one WAR document will get created and will cover data from the entire deployment.  The actual test results are accessible either through the question notes field, or through a S3 HTTP link.
4. The scripts will represent a subset of the WAR questions.  (Eventually all pillars covered)
5. The scripts will have the ability to output data to a readable text file for ingestion in a ticketing system

## Setup
Make certain that Python 3 is installed in your execution environment.  Once verified, you will need to install the boto3 package into Python.  You will do that using the command below:
```
pip3 install boto3
```

## Sample Scripts
Once Python3 and Boto3 are installed, you will run each of the scripts using the format of:
```
python3 {python script name} > {outputfilename}.json
```

T