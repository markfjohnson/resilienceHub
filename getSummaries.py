import boto3


client = boto3.client('resiliencehub')

response = client.list_apps(
    maxResults=90,
)
for a in response['appSummaries']:
    arn = a['appArn']
    response = client.describe_app_assessment(
        assessmentArn=arn
    )
    print(response)