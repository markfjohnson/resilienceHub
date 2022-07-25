import boto3
import json

client = boto3.client("resiliencehub")
apps = client.list_apps()['appSummaries']
for a in apps:
    print(a['appArn'])