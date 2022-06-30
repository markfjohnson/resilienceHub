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
