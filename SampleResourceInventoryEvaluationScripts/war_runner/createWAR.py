import boto3

client = boto3.client("wellarchitected")
response = client.create_workload(
    WorkloadName='MyTestWar',
    Description='Description',
    Environment='PRODUCTION',
    ReviewOwner='MFJ',
    AwsRegions=[
        "us-east-1"
    ],
    Lenses=[
    ],
    Tags={
        'Product': 'myProdct'
    }
)
print(response)
lenses = client.list_lenses()
answers = client.list_answers(
    WorkloadId=response['WorkloadId'],
    LensAlias='wellarchitected',
    PillarId='reliability'
)
print(answers)


