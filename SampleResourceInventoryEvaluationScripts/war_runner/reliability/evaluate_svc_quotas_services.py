import boto3
# This sample utility outputs to stdout a list of all ECS Services.  This is more for informational rather than compliance purposes.
import SampleResourceInventoryEvaluationScripts.war_runner.reliability.evaluate_redis_services as redis
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
