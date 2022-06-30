import reliability.evaluate_ecs_services as ecs_reliability
import reliability.evaluate_elbv2_services as elbv2_reliability
import reliability.evaluate_asg_services as asg_reliability
import reliability.evaluate_kinesis_services as kinesis_reliability
import reliability.evaluate_rds_services as rds_reliability
import reliability.evaluate_redis_services as redis_reliability
import reliability.evaluate_svc_quotas_services as svc_reliability
import reliability.evaluate_vpc_services as vpc_reliability

import SampleResourceInventoryEvaluationScripts.war_runner.common.evaluator_runner as er
import SampleResourceInventoryEvaluationScripts.war_runner.common.war_service as war
import SampleResourceInventoryEvaluationScripts.war_runner.reliability as ecs
import SampleResourceInventoryEvaluationScripts.war_runner.common.evaluator_runner as er


class evaluate_reliability_runner(er.evaluator_runner):
    productTag = ["Product"]



    def evaluate_ecs_multi_az(self):
        ecs_eval = ecs_reliability.evaluate_ecs_services()
        (ecs_clusters, tagList) = ecs_eval.setup(region="us-east-1", workloadTag=self.productTag)
        ecs_multi_az_issues = ecs_eval.evaluate(self.productTag, cluster=ecs_clusters)
        return(ecs_multi_az_issues)

    def evaluate_asg_multi_az(self):
        asg = asg_reliability.evaluate_asg_services()
        asg_groups = asg.setup("us-east-1")
        asg_issues = asg.evaluate(asg_groups, self.productTag)
        return(asg_issues)

    def evaluate_elbv2_multi_az(self):
        elb = elbv2_reliability.evaluate_elbv2_services()
        elb_groups = elb.setup("us-east-1")
        elb_issues = elb.evaluate(elb_groups, self.productTag)
        return(elb_issues)

    def evaluate_rds_multi_az(self):
        #TODO
        rds = rds_reliability.evaluate_rds_services()
        rds_groups = rds.setup("us-east-1")
        rds_issues = rds.evaluate(rds_groups, self.productTag)
        return(rds_issues)

    def evaluate_redis_multi_az(self):
        redis = redis_reliability.evaluate_redis_services()
        redis_groups = redis.setup("us-east-1")
        redis_issues = redis.evaluate(redis_groups, self.productTag)
        return(redis_issues)

    def evaluate_kinesis_multi_az(self):
        #TODO
        asg = asg_reliability.evaluate_asg_services()
        asg_groups = asg.setup("us-east-1")
        asg_issues = asg.evaluate(asg_groups, self.productTag)
        return(asg_issues)

    def evaluate_svc_quotas_multi_az(self):
        #TODO
        asg = asg_reliability.evaluate_asg_services()
        asg_groups = asg.setup("us-east-1")
        asg_issues = asg.evaluate(asg_groups, self.productTag)
        return(asg_issues)

    def evaluate_vpc_multi_az(self):
        #TODO
        asg = asg_reliability.evaluate_asg_services()
        asg_groups = asg.setup("us-east-1")
        asg_issues = asg.evaluate(asg_groups, self.productTag)
        return(asg_issues)


    def mergeResponsesByWorkloadTag(self, destList, newList):
        #TODO fix the merge
        for new_key in newList:
            key = new_key
            new_items = newList[key]
            if key in destList:
                destList[key] = new_items + destList[key]
            else:
                destList[key] = []
                destList[key] = new_items
        return(destList)


    def evaluate_all_multi_az(self):
        multiAZissues = {}
        self.mergeResponsesByWorkloadTag(multiAZissues, self.evaluate_ecs_multi_az())

        self.mergeResponsesByWorkloadTag(multiAZissues, self.evaluate_asg_multi_az())
        self.mergeResponsesByWorkloadTag(multiAZissues, self.evaluate_elbv2_multi_az())
        self.mergeResponsesByWorkloadTag(multiAZissues, self.evaluate_rds_multi_az())
        self.mergeResponsesByWorkloadTag(multiAZissues, self.evaluate_redis_multi_az())

        w = war.workload_service()
        answers = w.outputWARIssuesByWorkload("reliability", "fault-isolation",multiAZissues)
        return(multiAZissues)

    def evaluate_bulkhead_partitions(self):
        singleThread = self.evaluate_kinesis_multi_az()
        w = war()
        answers = w.outputWARIssuesByWorkload(singleThread)

    def evaluate_limits(self):
        limits = self.evaluate_svc_quotas_multi_az()
        w = war()



if __name__ == "__main__":
    e = evaluate_reliability_runner()
    multiAZissues = e.evaluate_all_multi_az()
    print(multiAZissues)

