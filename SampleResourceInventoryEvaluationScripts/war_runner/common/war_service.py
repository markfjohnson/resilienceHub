import boto3
import json


class workload_service:
    client = None
    CHOICE_BLANK = ['rel_fault_isolation_no']
    CHOICE_MULTI_AZ = ["rel_fault_isolation_multiaz_region_system",
                       "rel_fault_isolation_select_location"]

    def __init__(self):
        self.client = boto3.client("wellarchitected")

    def getWorkloadQuestion(self, workLoadName, pillar, question):
        response = self.client.list_workloads(
            WorkloadNamePrefix=workLoadName,
        )
        workloadId = response['WorkloadSummaries'][0]['WorkloadId']
        response = self.client.list_answers(
            WorkloadId=workloadId,
            LensAlias='wellarchitected',
            PillarId=pillar,
        )
        print(response)
        response = self.client.get_answer(
            WorkloadId=workloadId,
            LensAlias='wellarchitected',
            QuestionId=question)
        return (response['Answer'])

    def getWorkloadId(self, workloadName):
        response = self.client.list_workloads(
            WorkloadNamePrefix=workloadName,
        )
        if len(response['WorkloadSummaries']) == 1:
            workloadId = response['WorkloadSummaries'][0]['WorkloadId']
        else:
            response = self.client.create_workload(
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

        return (workloadId)

    def outputAnswer(self, workload_id, pillar, question, choices, turn_on=True, note=""):
        c = self.client.get_answer(WorkloadId=workload_id, LensAlias='wellarchitected', QuestionId=question)
        a = c['Answer']
        choiceList = a['SelectedChoices']
        new_selection = []
        if self.CHOICE_BLANK[0] not in choiceList:
            if turn_on == True:
                if self.CHOICE_BLANK[0] not in choices:
                    new_selection = list(set(choiceList + choices))
                else:
                    new_selection = choices
            elif turn_on == False:
                new_selection = [x for x in choiceList if x not in choices]
        else:
            if self.CHOICE_BLANK[0] not in choices:
                if turn_on == True:
                    new_selection = list(set(choiceList + choices))
                elif turn_on == False:
                    new_selection = [x for x in choiceList if x not in choices]
            else:
                new_selection = choices

        response = self.client.update_answer(
            WorkloadId=workload_id,
            LensAlias='wellarchitected',
            QuestionId=question,
            SelectedChoices=new_selection,
            Notes=note
        )
        return (response)

    def buildAnswerChoices(self, currentChoices, newChoices, turn_on=True):
        """
        Merges new choices into the questions current choices.  If the new set of responses for the answer invalidates
        a previously selected option, then the affiliated answers are unselected and the "None of these" option is
        selected.
        :param currentChoices:
        :param newChoices:
        :return:
        """
        merged_choices = []
        if self.CHOICE_BLANK[0] not in currentChoices:
            if turn_on == True:
                if self.CHOICE_BLANK[0] not in newChoices:
                    merged_choices = list(set(currentChoices + newChoices))
                else:
                    merged_choices = newChoices
            elif turn_on == False:
                merged_choices = [x for x in currentChoices if x not in newChoices]
        else:
            if self.CHOICE_BLANK[0] not in newChoices:
                if turn_on == True:
                    merged_choices = list(set(currentChoices + newChoices))
                elif turn_on == False:
                    merged_choices = [x for x in currentChoices if x not in newChoices]
            else:
                merged_choices = newChoices

        return merged_choices


    def outputWARIssuesByWorkload(self, pillar, question, issues):
        """
        ASSUMPTION: All of the issues have the same question and pillar
        """
        answerList = []
        for key in issues:
            workloadIssues = issues[key]
            workloadId = self.getWorkloadId(key)

            if len(workloadIssues) == 0:
                resp = self.outputAnswer(workload_id=workloadId, pillar=pillar, question=question,
                                         choices=self.CHOICE_MULTI_AZ, turn_on=True,
                                         note=f"WAR_SCAN: Scanned services supported multi-AZ")
            else:
                resp = self.outputAnswer(workload_id=workloadId, pillar=pillar, question=question,
                                         choices=self.CHOICE_BLANK, turn_on=True,
                                         note=json.dumps(workloadIssues))


            answerList.append(resp)
        return (answerList)

    # def enterBlankAnswer(self, workloadId, pillar, question, workloadIssues):
    #     cur_answer = self.client.get_answer(
    #         WorkloadId=workloadId,
    #         LensAlias='wellarchitected',
    #         QuestionId=question)['Answer']
    #
    #     selected_options = []
    #     if len(cur_answer['SelectedChoices']) == 0:
    #         selected_options = self.CHOICE_BLANK
    #     else:
    #         selected_options = cur_answer['SelectedChoices']
    #     resp = self.outputAnswer(workloadId, pillar, question,
    #                              selected_options,
    #                              f"WAR_SCAN: {len(workloadIssues)} services are not configured for multi-AZ\n" + json.dumps(
    #                                  workloadIssues))
    #     return (resp)

    def deleteWorkload(self, workloadName):
        workloadId = self.getWorkloadId(workloadName)
        response = self.client.delete_workload(
            WorkloadId=workloadId
        )
        return (response)
