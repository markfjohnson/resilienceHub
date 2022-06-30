from unittest import TestCase
import boto3
import moto
import pandas as pd

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
        invalid_resources = []
        for c in elbs['LoadBalancers']:
            productValue = None
            lb_tags = self.client.describe_tags(
                ResourceArns=[
                    c['LoadBalancerArn'],
                ]
            )
            for tlb in lb_tags['TagDescriptions']:
                for t in tlb['Tags']:
                    if t['Key'] in workloadTags:
                        productValue = t['Value']

            if c['Scheme'] == 'internet-facing':
                k = {
                    "LoadBalancerName": c['LoadBalancerName'],
                    "DNSName": c['DNSName'],
                    "IpAddressType": c['IpAddressType'],
                    "Product": productValue
                }
                invalid_resources.append(k)

        return(invalid_resources)

if __name__ == "__main__":
    l = evaluate_elbv2_services()
    elb_list = l.setup("us-east-1")
    invalid_responses = l.evaluate(elb_list, ["Product"] )
    df = pd.DataFrame.from_dict(invalid_responses)
    df.to_excel('medidata-lb-endpoints.xlsx')
    print(invalid_responses)

