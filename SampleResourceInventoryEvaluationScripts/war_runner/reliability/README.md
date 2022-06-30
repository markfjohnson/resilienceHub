# Reliability WAR Evaluation scripts

The scripts contained in this directory evaluate different aspects around Reliability in the customer's environment.  

The execution of these scripts all follow the same pattern which is described in the project Parenet README.md file.

## High Availability

High availability scripts consists of 2 flavors Multi-AZ and Multi-Region.  Services covered by the scripts include:
 - Autoscaling Groups
 - ECS
 - Elastic Load Balancer v2
 - RDS cluster
 - Redis Cluster

### Multi-AZ evaluation scripts
- (Done) Load balancer across multiple AZs
- AWS Managed service has Multi-AZ option enabled

TODO Complete EKS script(s)
A customer's application/service needs to be Multi-AZ if it is deployed to a VPC SubNet.  Services evaluated for Multi-AZ HA compliance include the following list

The sample scripts to highlight Multi-AZ HA compliance issues are listed below:

| Script Name                     | Service tested | Test condition                                                                   |
|---------------------------------|----------|----------------------------------------------------------------------------------|
| evaluate-ecs-services.py        | ecs services | desiredCount < 2 or placementStrategy != 'spread') |
| evaluate-elbv2-services.py      | elastic load balancer v2 | azCount < 2 |
| evaluate-rds-deployments.py     | rds (non-read replicas) | (isReadReplica == False and (multiAZ == False or subnetCount <= 1)) |
| evaluate-redis-deployments.py | Elasticache - Redis Cluster | (multiAZ != 'enabled' or nodeCount <= 1 ) |   


### Multi-Region evaluation scripts
- Multi-region database replication
  - Neptune to Neptune cross region access 
- *Route53 DNS pointing to load balancer or api gateway

### Multi-threaded Messaging
- (Done) Kinesis has more than 1 shard
- (?) More than 1 ECS client reading from Kafka, Kinesis, or other messaging system

| Script Name                     | Service tested | Test condition                                                                   |
|---------------------------------|----------|----------------------------------------------------------------------------------|
| evaluate-kinesis-deployments.py | Kinesis | shardCnt <= 1 |


### Multiple external connections
- Multiple Direct Connects
- Multiple VPNs

### Scalable resources

| Script Name                     | Service tested | Test condition                                                                   |
|---------------------------------|----------|----------------------------------------------------------------------------------|
| evaluate-asg-services.py        | autoscaling groups    | minSize < 2 or (maxSize == minSize) or (azCount < 2) or (maxSize <= desiredSize) |

### Well Planned Network topology
- *IP CIDR range is reasonable for the number of instances within a tag group (Only if tag group option is enabled for scripts)
- *Scan VPCs for overlapping CIDR ranges


| Script Name              | Service tested | Test condition               |
|--------------------------|----------------|------------------------------|
| evaluate-vpc-services.py | VPC            | Check for overlapping ranges |


## Manage Service quotas
| Script Name                     | Service tested | Test condition               |
|---------------------------------|----------------|------------------------------|
| evaluate-svc-quotas-services.py | VPC            | Check for overlapping ranges |

#TODO figure out response object


### Approaching quotas (Soft and Hard) (Low)
- Check resource consumption for each service against the current table
- Enable EventBridge to monitor for quota events

### Failure Migation
- Are container insights turned on? You cannot have failure mitigation on ECS and EKS without container insights
  - Get Cloudwatch container metrics
- Lambda event source batch size greater than 1 with some form of dead letter queue enabled
- Check for exponential backoff retries (#TODO how do we do this)
- Check for existence and type of LB and ASG healthchecks.  Ensure healthcheck for all open LB ports
