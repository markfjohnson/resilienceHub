from unittest import TestCase
import boto3
import SampleResourceInventoryEvaluationScripts.war_runner.common.evaluator_runner as er


class evaluate_kinesis_services(er.evaluator_runner):
    region='us-east-1'
    client = None

    def setup(self, region):
        self.client = boto3.client('kinesis', region_name=region)
        ProductKey = "Product"
        kds_streams = self.client.list_streams()
        return(kds_streams)

    def evaluate(self, kds_streams, workloadTags):
        invalid_resources = {}
        kds_single_shard_list = []
        for s in kds_streams['StreamNames']:
            kds = self.client.describe_stream(StreamName=s)
            kds_tags = self.client.list_tags_for_stream(
                StreamName=s
            )
            productValue = None
            for t in kds_tags['Tags']:
                if t['Key'] in workloadTags:
                    productValue = t['Value']

            shardCnt = len(kds['StreamDescription']['Shards'])
            if shardCnt <= 1:
                k = {
                    "StreamName": kds['StreamDescription']['StreamName'],
                    "StreamStatus": kds['StreamDescription']['StreamStatus'],
                    "ShardCount": shardCnt,
                    "RetentionPeriodHours": kds['StreamDescription']['RetentionPeriodHours'],
                    "WhyTriggered": f"Kinesis should have > 1 shard...currently {shardCnt} shards",
                    "Product": productValue,
                }
                if productValue not in invalid_resources:
                    invalid_resources[productValue] = []
                    invalid_resources[productValue].append(k)
                else:
                    invalid_resources[productValue].append(k)

        return(invalid_resources)

if __name__ == "__main__":
    k = evaluate_kinesis_services()
    kinesis_data_streams = k.setup(region="us-east-1")
    invalid_response = k.evaluate(kds_streams=kinesis_data_streams, workloadTags=['Product'])
    print(invalid_response)