
class evaluator_runner:
    def outputAnswer(client, workload_id, pillar, question, choices, note):
        choiceList = []
        for c in choices:
            choiceList.append({c: {'Status':'SELECTED', "Notes":note}})

        response = client.update_answer(
            WorkloadId=workload_id,
            LensAlias='wellarchitected',
            QuestionId=question,

            SelectedChoices=choices,
            Notes=note
        )
        return(response)

    def getWorkloadId(self, client, workloadName):

        response = client.list_workloads(
            WorkloadNamePrefix=workloadName,
        )
        if len(response['WorkloadSummaries']) == 1:
            workloadId = response['WorkloadSummaries'][0]['WorkloadId']
        else:

            response = client.create_workload(
                WorkloadName=workloadName,
                Description='Description',
                Environment='PRODUCTION',
                ReviewOwner='MFJ',
                AwsRegions=[
                    "us-east-1"
                ],
                Lenses=[
                ],
                Tags={
                    'WARRUNNER': workloadName
                }
            )
            workloadId = response['WorkloadId']

        return(workloadId)

