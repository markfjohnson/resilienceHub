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
import SampleResourceInventoryEvaluationScripts.war_runner.common.evaluator_runner as er

class evaluate_svc_quotas_services(er.evaluator_runner):
    region='us-east-1'
    ProductKey = "Product"
    client = None

    def setup(self, region):
        # Check for history of changes covers 'Aware of service quotas and constraints"
        # NOTE: This evaluation is not product tag specific
        self.client = boto3.client('service-quotas', region_name=region)

        svc_list = self.client.list_requested_service_quota_change_history()
        return(svc_list)

    def evaluate(self, svc_list):
        #TODO Figure out how to make this check meaningful
        invalid_resources = {}

        return []
