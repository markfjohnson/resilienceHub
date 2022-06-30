import boto3
import json
import os.path, sys

import SampleResourceInventoryEvaluationScripts.war_runner.common.evaluator_runner as er
import SampleResourceInventoryEvaluationScripts.war_runner.common.war_service as war

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

class evaluate_ecs_services(er.evaluator_runner):
    region = "us-east-1"
    workloadTag = None
    client = None

    def setup(self, region, workloadTag):
        self.region = region
        self.workloadTag = workloadTag
        self.client = boto3.client('ecs', region_name=region)
        clusters_list = self.client.list_clusters()
        ecs_clusters = self.client.describe_clusters(clusters=clusters_list['clusterArns'])
        # TODO Get the Workload Tags
        workloadTagList = []
        return (ecs_clusters['clusters'], workloadTagList)



    def evaluate(self, workloadTag, cluster):
        invalid_resources = {}
        for c in cluster:
            ecs_services = self.client.list_services(cluster=c['clusterArn'])

            if len(ecs_services['serviceArns']) > 0:
                services_def = self.client.describe_services(cluster=c['clusterArn'],
                                                             services=ecs_services['serviceArns'])

            for s in services_def['services']:
                ecs_svc_tags = self.client.list_tags_for_resource(resourceArn=s['serviceArn'])
                productValue = None
                for t in ecs_svc_tags['tags']:
                    if t['key'] in workloadTag:
                        productValue = t['value']
                desiredCount = s['desiredCount']

                # TODO modify the line below to support a list of placement strategies
                if len(s['placementStrategy']) > 0:
                    placementStrategy = s['placementStrategy'][0]['type']
                else:
                    placementStrategy = ""
                if (desiredCount < 2 or placementStrategy != 'spread'):
                    reason = ""
                    if desiredCount < 2:
                        reason = reason + "There must be more than one task deployed for each service"

                    if placementStrategy != 'spread':
                        reason = reason + "The service tasks must be spread across ECS instances"

                    k = {
                        "clusterName": c['clusterName'],
                        "status": c['status'],
                        "PillarId": "reliability",
                        "QuestionId": "fault-isolation",
                        "registeredContainerInstancesCount": c['registeredContainerInstancesCount'],
                        "activeServicesCount": c['activeServicesCount'],
                        "capacityProviders": c["capacityProviders"],
                        "serviceName": s['serviceName'],
                        "status": s['status'],
                        "placementConstraints": s["placementConstraints"],
                        "placementStrategy": placementStrategy,
                        "desiredCount": desiredCount,
                        "enableECSManagedTags": s['enableECSManagedTags'],
                        "enableECSManagedTags": s['enableECSManagedTags'],
                        "product": productValue,
                        "WhyTriggered": reason
                    }
                    if productValue not in invalid_resources:
                        invalid_resources[productValue] = []
                        invalid_resources[productValue].append(k)
                    else:
                        invalid_resources[productValue].append(k)

        return (invalid_resources)


if __name__ == "__main__":
    productTag = "Product"
    pillar = 'reliability'
    question = 'fault-isolation'
    ecs_eval = evaluate_ecs_services()
    w = war.workload_service()

    (ecs_clusters, workloadTagList) = ecs_eval.setup(region="us-east-1", workloadTag="Product")
    invalid_responses = ecs_eval.evaluate(cluster=ecs_clusters, workloadTag=productTag)

    #w.outputWARIssuesByWorkload( pillar, question,invalid_responses)
    print(json.dumps(invalid_responses, indent=4, sort_keys=True))


