import boto3
import argparse
import json

client = boto3.client("resiliencehub")
apps = client.list_apps()

for a in apps['appSummaries']:
    try:
        appArn = a['appArn']
        print(appArn)
        response = client.list_app_versions(
            appArn=appArn
        )
        versionNumber = len(response['appVersions']) - 1
        response = client.list_unsupported_app_version_resources(
            appArn=appArn,
            appVersion=str(versionNumber),
        )
        print(response)

    except Exception:
        print("Can't resolve this one")