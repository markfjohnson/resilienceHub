import boto3

import SampleResourceInventoryEvaluationScripts.war_runner.common.evaluator_runner as er



class evaluate_asg_services(er.evaluator_runner):

    region = "us-east-1"
    workloadTag = None
    client = None

    def setup(self, region):
        self.client = boto3.client('autoscaling', region_name=region)
        asg_groups = self.client.describe_auto_scaling_groups()
        return(asg_groups)

    def evaluate(self, asg_groups, workloadTag):
        invalid_resources = {}
        for c in asg_groups['AutoScalingGroups']:
            minSize = c['MinSize']
            desiredSize = c['DesiredCapacity']
            maxSize = c['MaxSize']
            activeInstances = len(c['Instances'])
            azCount = len(c['AvailabilityZones'])

            productValue = None
            propagateAtLaunch = "False"
            for t in c['Tags']:
                if t['Key'] in workloadTag:
                    productValue = t['Value']
                    propagateAtLaunch = t['PropagateAtLaunch']

            if minSize < 2 or (maxSize == minSize) or (azCount < 2) or (maxSize <= desiredSize):
                reason = ""
                if minSize < 2:
                    reason = reason + "MinSize should be 2 or greater. "

                if (maxSize <= minSize):
                    reason = reason + "MaxSize should not be the same as the minSize. "

                if (maxSize <= desiredSize):
                    reason = reason + "maxSize cannot be equal to or less than the desired capacity size. "

                if azCount < 2:
                    reason = reason + "You must have more than 2 availability zones for Multiple AZ HA. "

                k = {
                    "AutoScalingGroupName": c['AutoScalingGroupName'],
                    "minSize": minSize,
                    "maxSize": maxSize,
                    "desiredSize": desiredSize,
                    "AZcount": azCount,
                    "activeInstances": activeInstances,
                    "healthCheckType": c['HealthCheckType'],
                    "DefaultCooldown": c['DefaultCooldown'],
                    "Product": productValue,
                    "PropagateProductTagAtLaunch": propagateAtLaunch,
                    "WhyTriggered": reason
                }

                if productValue not in invalid_resources:
                    invalid_resources[productValue] = []
                    invalid_resources[productValue].append(k)
                else:
                    invalid_resources[productValue].append(k)
        return(invalid_resources)

if __name__ == "__main__":
    e = evaluate_asg_services()
    asg_groups = e.setup(region="us-east-1")
    invalid_response = e.evaluate(asg_groups=asg_groups,workloadTag=['Product'])
    print(invalid_response)




