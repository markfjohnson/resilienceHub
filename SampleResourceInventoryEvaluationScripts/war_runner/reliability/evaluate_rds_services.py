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


class evaluate_rds_services(er.evaluator_runner):
    region='us-east-1'
    ProductKey = "Product"
    client = None

    def setup(self, region):
        self.client = boto3.client('rds', region_name=region)
        db_clusters = self.client.describe_db_instances()
        return(db_clusters['DBInstances'])

    def evaluate(self, db_clusters, workloadTag):
        invalid_resources = {}
        for c in db_clusters:
            multiAZ = c['MultiAZ']
            readReplicaIdentifier = c.get('ReadReplicaSourceDBInstanceIdentifier')
            productValue = None
            for t in c['TagList']:
                if t['Key'] in workloadTag:
                    productValue = t['Value']

            if readReplicaIdentifier == None:
                isReadReplica = False
            else:
                isReadReplica = True if len(c.get('ReadReplicaSourceDBInstanceIdentifier'))>0 else False

            subnetCount = len(c.get('DBSubnetGroup')['Subnets'])
            if (isReadReplica == False and (multiAZ == False or subnetCount <= 1)):
                reason =""
                if (multiAZ == False):
                    reason=reason + "RDS does not have multiAZ. "
                if (subnetCount <= 1):
                    reason = reason + "RDS requires more than 1 Subnet to support MultiAZ"

                k = {
                    "DBInstanceIdentifier": c['DBInstanceIdentifier'],
                    "isReadReplica": isReadReplica,
                    "DBName": c["DBName"],
                    "Engine": c['Engine'],
                    "multiAZ": multiAZ,
                    "SubnetCounts": subnetCount,
                    "Product": productValue,
                    "WhyTriggered": reason

                }
                if productValue not in invalid_resources:
                    invalid_resources[productValue] = []
                    invalid_resources[productValue].append(k)
                else:
                    invalid_resources[productValue].append(k)
        return(invalid_resources)

if __name__ == "__main__":
    r = evaluate_rds_services()
    rds_clusters = r.setup(region="us-east-1")
    invalid_response = r.evaluate(db_clusters=rds_clusters, workloadTag=['Product'])
    print(invalid_response)
