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


import boto3
import moto
import pandas as pd

import SampleResourceInventoryEvaluationScripts.war_runner.reliability.evaluate_asg_services as asgr
import SampleResourceInventoryEvaluationScripts.war_runner.common.war_service as war
import SampleResourceInventoryEvaluationScripts.war_runner.common.evaluator_runner as er

class evaluate_apigw_services(er.evaluator_runner):

    region='us-east-1'
    ProductKey = "Product"
    client = None

    def setup(self, region):
        self.client = boto3.client('apigatewayv2', region_name=region)
        apis = self.client.get_apis()
        return(apis)

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
    l = evaluate_apigw_services()
    elb_list = l.setup("us-east-1")
    invalid_responses = l.evaluate(elb_list, ["Product"] )
    df = pd.DataFrame.from_dict(invalid_responses)
    df.to_excel('medidata-lb-endpoints.xlsx')
    print(invalid_responses)

