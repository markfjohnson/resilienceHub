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


class evaluate_redis_services(er.evaluator_runner):
    region='us-east-1'
    client = None

    def setup(self, region):
        self.client = boto3.client('elasticache', region)
        cache_clusters = self.client.describe_replication_groups()
        return(cache_clusters)

    def evaluate(self, cache_clusters, workloadTags):
        invalid_resources = {}
        for c in cache_clusters['ReplicationGroups']:
            multiAZ = c['MultiAZ']
            autoFailover = c['AutomaticFailover']
            nodeCount = len(c['MemberClusters'])
            if (multiAZ != 'enabled' or nodeCount <= 1 ):
                reason = ""
                if multiAZ != "enabled":
                    resason = reason + "RDS does not have multiAZ set to 'enabled'.  if Multi-AZ is enabled, the downtime is minimized. The role of primary node will automatically fail over to one of the read replicas. "
                if nodeCount <= 1:
                    reason = reason + "Redis must have more than 1 MemberCluster. "

                k = {
                    "ReplicationGroupId": c['ReplicationGroupId'],
                    "AutomaticFailover": autoFailover,
                    "multiAZ": multiAZ,
                    "Status": c['Status'],
                    "ClusterNodeCounts": nodeCount,
                    "ClusterEnabled": c['ClusterEnabled'],
                    "WhyTriggered": reason
                }
                #TODO include the list_resource_tags to get the tags and produce a proper invalid_resource output
                productValue = "ALL"
                if productValue not in invalid_resources:
                    invalid_resources[productValue] = []
                    invalid_resources[productValue].append(k)
                else:
                    invalid_resources[productValue].append(k)
        return(invalid_resources)

