# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
from unittest import TestCase
import boto3
import moto

import SampleResourceInventoryEvaluationScripts.war_runner.reliability.evaluate_asg_services as asgr
import SampleResourceInventoryEvaluationScripts.war_runner.common.war_service as war
import SampleResourceInventoryEvaluationScripts.war_runner.common.evaluator_runner as er

class evaluate_elbv2_services(er.evaluator_runner):

    region='us-east-1'
    ProductKey = "Product"
    client = None

    def setup(self, region):
        self.client = boto3.client('elbv2', region_name=region)
        elbs = self.client.describe_load_balancers()
        return(elbs)

    def evaluate(self, elbs, workloadTags):
        invalid_resources = {}
        for c in elbs['LoadBalancers']:
            lb_tags = self.client.describe_tags(
                ResourceArns=[
                    c['LoadBalancerArn'],
                ]
            )
            productValue = None
            for tlb in lb_tags['TagDescriptions']:
                for t in tlb['Tags']:
                    if t['Key'] in workloadTags:
                        productValue = t['Value']


            azCount = len(c['AvailabilityZones'])
            if azCount < 2:
                k = {
                    "LoadBalancerName": c['LoadBalancerName'],
                    "DNSName": c['DNSName'],
                    "Scheme": c['Scheme'],
                    "VpcId": c['VpcId'],
                    "Type": c['Type'],
                    "azCount": azCount,
                    "Product": productValue,
                    "WhyTriggered": "MultiAZ requires at least 2 Availability Zones."
                }
                if productValue not in invalid_resources:
                    invalid_resources[productValue] = []
                    invalid_resources[productValue].append(k)
                else:
                    invalid_resources[productValue].append(k)

        return(invalid_resources)

if __name__ == "__main__":
    l = evaluate_elbv2_services()
    elb_list = l.setup("us-east-1")
    invalid_responses = l.evaluate(elb_list, ["Product"] )

