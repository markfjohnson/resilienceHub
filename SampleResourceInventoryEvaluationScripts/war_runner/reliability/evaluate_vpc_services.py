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
from ipaddress import IPv4Network
# This sample utility outputs to stdout a list of all ECS Services.  This is more for informational rather than compliance purposes.
import SampleResourceInventoryEvaluationScripts.war_runner.common.evaluator_runner as er

class evaluate_vpc_services(er.evaluator_runner):
    region='us-east-1'
    ProductKey = "Product"

    def setup(self, region):
        self.client = boto3.client('ec2', region_name=region)
        vpc_list = self.client.describe_vpcs()

        return(vpc_list['Vpcs'])

    def evaluate(self, vpc_list):
        invalid_resources = {}
        cidr_list = {}

        for v in vpc_list:
            vpcId = v['VpcId']
            subnet_list = self.client.describe_subnets(Filters=[{'Name':'vpc-id','Values':[vpcId]}])

            cnt = 1
            for cidr in subnet_list['Subnets']:
                n = IPv4Network(cidr['CidrBlock'])
                cidr_list[n] = []
                cidr_list[n] = f"Net{cnt}"
                cnt = cnt+1

            networks_list = sorted(cidr_list.keys())
            prev_network = networks_list.pop(0)
            for current_network in networks_list:
                if prev_network.overlaps(current_network):
                    print("Network {} overlaps {}".format(prev_network, current_network))
                    k = {'VpcId': vpcId, 'cidrBlock': cidr['CidrBlock'], "state": cidr['CidrBlockState']['State']}
                    productValue = "ALL"
                    if productValue not in invalid_resources:
                        invalid_resources[productValue] = []
                        invalid_resources[productValue].append(k)
                    else:
                        invalid_resources[productValue].append(k)
                prev_network = current_network


        return(invalid_resources)

if __name__ == "__main__":
    v = evaluate_vpc_services()
    vpc_list = v.setup(region="us-east-1")
    invalid_response = v.evaluate(vpc_list=vpc_list)
    print(invalid_response)


