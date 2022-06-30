import os.path

from aws_cdk.aws_s3_assets import Asset

from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_s3 as s3,
    aws_logs as logs,
    aws_ecs as ecs,
    aws_rds as rds,
    aws_s3_deployment as s3deploy,
    aws_elasticloadbalancingv2 as elbv2,
    aws_autoscaling as autoscaling,
    aws_kms as kms,
    aws_kinesis as kinesis,
    Tags as tags,

    App, Stack, RemovalPolicy
)

import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_ecs_patterns as ecsp

from constructs import Construct


class ResilienceHubStack(Stack):
    defaultInstanceType = "t2.micro"
    product = "MyProduct"

    def defineNetworkStuff(self, vpcName, projectTag):
        log_group = logs.LogGroup(self, f"{vpcName}VPCLogGroup", retention=logs.RetentionDays.THREE_DAYS)
        flowIAM = iam.Role(self, f"{vpcName}FlowRole", assumed_by=iam.ServicePrincipal("vpc-flow-logs.amazonaws.com"))

        # VPC
        pubSubnet = ec2.SubnetConfiguration(name=f"{vpcName}public", subnet_type=ec2.SubnetType.PUBLIC)
        subnets = []
        subnets.append(pubSubnet)
        privateSubnet = ec2.SubnetConfiguration(name=f"{vpcName}private", subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT)
        subnets.append(privateSubnet)
        vpc = ec2.Vpc(self, f"{vpcName}VPC", max_azs=3,
                      subnet_configuration=subnets)
        ec2.FlowLog(self, f"{vpcName}FlowLog",
                    resource_type=ec2.FlowLogResourceType.from_vpc(vpc),
                    destination=ec2.FlowLogDestination.to_cloud_watch_logs(log_group, flowIAM))
        tags.of(vpc).add("Product", projectTag);
        #        tags.of(pubSubnet).add("Product", projectTag);
        #        tags.of(privateSubnet).add("Product", projectTag);
        return (vpc, pubSubnet, privateSubnet)

    def defineSecurityGroup(self, secgroupName, vpc, projectTag):
        # create a new security group
        sec_group = ec2.SecurityGroup(
            self,
            secgroupName,
            vpc=vpc,
            allow_all_outbound=True,
        )

        # add a new ingress rule to allow port 22 to internal hosts
        sec_group.add_ingress_rule(
            peer=ec2.Peer.ipv4('10.0.0.0/16'),
            description="Allow SSH connection",
            connection=ec2.Port.tcp(22)
        )
        tags.of(sec_group).add("Product", projectTag)

        return (sec_group)

    def defineECScluster(self, clusterName, vpc, subnets, asg, projectTag):
        vpc.select_subnets(
            subnet_type=ec2.SubnetType.PUBLIC
        )
        cluster = ecs.Cluster(self, f"{clusterName}Cluster",
                              vpc=vpc
                              )
        cp = cluster.add_capacity(f"{clusterName}AutoScalingGroupCapacity", auto_scaling_group_name=f"{clusterName}ASG",
                                  instance_type=ec2.InstanceType("t3.micro"),
                                  desired_capacity=1, min_capacity=1, max_capacity=3,
                                  key_name="mfj-ecs-cluster"
                                  )
        tags.of(cp).add("Product", projectTag)
        tags.of(cluster).add("Product", projectTag)
        return (cluster)

    def defineEcsTaskDefinition(self, taskName):
        Fail

    def defineEcsService(self, clusterName, ecsService, vpc, td, desired_count=2):
        service = ecs.Ec2Service(self, ecsService, cluster=clusterName, task_definition=td, desired_count=desired_count)

        lb = elbv2.LoadBalancer(self, "LB", vpc=vpc)
        lb.add_listener(external_port=80)
        lb.add_target(service.load_balancer_target(
            container_name="MyContainer",
            container_port=80
        ))
        return (service, lb)

    def defineASGLoadBalancer(self, lbName, sg, vpc, sn1, sn2, projectTag):
        role = iam.Role(self, f"{lbName}InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        asg = autoscaling.AutoScalingGroup(self, f"{lbName}ASG",
                                           vpc=vpc,
                                           auto_scaling_group_name=lbName,
                                           instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2,
                                                                             ec2.InstanceSize.MICRO),
                                           machine_image=ec2.AmazonLinuxImage(),
                                           security_group=sg,
                                           desired_capacity=1,
                                           max_capacity=3,
                                           role=role,
                                           key_name="mfj-ecs-cluster",
                                           min_capacity=0
                                           )

        tags.of(asg).add("Product", projectTag)
        tags.of(asg).add("Patch Group", "C")
        tags.of(asg).add("SSMManager", "True")
        # Create the load balancer in a VPC. 'internetFacing' is 'false'
        # by default, which creates an internal load balancer.
        lb = elbv2.ApplicationLoadBalancer(self, f"{lbName}LB",
                                           vpc=vpc,
                                           internet_facing=True,
                                           vpc_subnets=ec2.SubnetSelection(
                                               subnet_type=ec2.SubnetType.PUBLIC
                                           ), load_balancer_name=lbName, security_group=sg,

                                           )
        tags.of(lb).add("Product", projectTag)

        # Add a listener and open up the load balancer's security group
        # to the world.
        listener = lb.add_listener(f"{lbName}Listener",
                                   port=80,
                                   open=True,
                                   )

        # Create an AutoScaling group and add it as a load balancing
        # target to the listener.
        listener.add_targets(f"{lbName}ApplicationFleet",
                             port=8080,
                             targets=[asg]
                             )
        return (lb)

    def defineEC2Instance(self, instanceName, vpc, subnet, sec_group, projectTag):
        # AMI
        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
        )
        role = iam.Role(self, f"{instanceName}InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        # define a new ec2 instance
        ec2_instance = ec2.Instance(
            self,
            instanceName,
            instance_name=instanceName,
            instance_type=ec2.InstanceType(ResilienceHubStack.defaultInstanceType),
            machine_image=amzn_linux,
            vpc=vpc,
            role=role,
            key_name="mfj-ecs-cluster",
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            security_group=sec_group,
        )
        tags.of(ec2_instance).add("Product", projectTag)
        return (ec2_instance)

    def defineRedisCluster(self):
        # TODO Define this
        pass

    def defineLambdaNoConcurrency(self):
        # TODO Define this
        pass

    def defineLambdaConcurrency(self):
        # TODO Define this
        pass

    def defineKinesisOneShard(self, name):
        key = kms.Key(self, f"{name}KinesisOneShardKMS")

        kds = kinesis.Stream(self, f"{name}KinesisOneShardKDS",
                             encryption=kinesis.StreamEncryption.KMS,
                             encryption_key=key,
                             shard_count=1
                             )
        tags.of(kds).add("Product", self.product);

        return (kds)

    def defineKinesisMultiShard(self, name):
        key = kms.Key(self, f"{name}KinesisMultiShardKMS")

        kds = kinesis.Stream(self, f"{name}KinesisMultiShardKDS",
                             encryption=kinesis.StreamEncryption.KMS,
                             encryption_key=key,
                             shard_count=3
                             )
        tags.of(kds).add("Product", self.product);

        return (kds)

    def defineLambdaSQSEventSourceBatch1(self):
        # TODO Define this
        pass

    def defineLambdaSNSEventSourceBatch1(self):
        # TODO Define this
        pass

    def defineLambdaKinesisEventSourceBatch1(self):
        # TODO Define this
        pass

    def defineRDSMySQLNoMultiAz(self, name, vpc):
        instance = rds.DatabaseInstance(self, name,
                                        engine=rds.DatabaseInstanceEngine.mysql(
                                            version=rds.MysqlEngineVersion.VER_8_0_21
                                        ),
                                        instance_type=ec2.InstanceType("m5.4xlarge"),
                                        vpc=vpc,
                                        multi_az=False,
                                        database_name=name,
                                        publicly_accessible=True,
                                        allocated_storage=100,
                                        storage_type=rds.StorageType.GP2,
                                        cloudwatch_logs_exports=["error", "general", "slowquery"],
                                        deletion_protection=False,
                                        enable_performance_insights=True,
                                        delete_automated_backups=True,
                                        parameter_group=rds.ParameterGroup.from_parameter_group_name(
                                            self, f"{name}para-group-mysql",
                                            parameter_group_name="default.mysql8.0"
                                        )
                                        )
        tags.of(instance).add("Product", self.product);
        return (instance)

    def defineRDSMySQLMultiAz(self, name, vpc):
        instance = rds.DatabaseInstance(self, name,
                                        engine=rds.DatabaseInstanceEngine.mysql(
                                            version=rds.MysqlEngineVersion.VER_8_0_21
                                        ),
                                        instance_type=ec2.InstanceType("m5.4xlarge"),
                                        vpc=vpc,
                                        database_name=name,
                                        multi_az=True,
                                        publicly_accessible=True,
                                        allocated_storage=100,
                                        storage_type=rds.StorageType.GP2,
                                        cloudwatch_logs_exports=["error", "general", "slowquery"],
                                        deletion_protection=False,
                                        enable_performance_insights=True,
                                        delete_automated_backups=True,
                                        parameter_group=rds.ParameterGroup.from_parameter_group_name(
                                            self, f"{name}para-group-mysql",
                                            parameter_group_name="default.mysql8.0"
                                        )
                                        )
        tags.of(instance).add("Product", self.product);
        return (instance)

    def defineRDSMySQLDBCloud(self, name, vpc):
        instance = rds.DatabaseInstance(self, name,
                                        engine=rds.DatabaseInstanceEngine.MYSQL(
                                            version=rds.MysqlEngineVersion.VER_5_7_34),
                                        # optional, defaults to m5.large
                                        instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2,
                                                                          ec2.InstanceSize.SMALL),

                                        vpc=vpc,
                                        max_allocated_storage=200,
                                        database_name=name
                                        )
        tags.of(instance).add("Product", self.product);
        return (instance)

    def defineBucket(self, bucket_name):
        s3Bucket = s3.Bucket(self, "mdd-sampleData", auto_delete_objects=True,
                             removal_policy=RemovalPolicy.DESTROY,
                             bucket_name=bucket_name
                             )
        tags.of(s3Bucket).add("Product", self.product);
        return (s3Bucket)

    def twoEC2(self):
        tn = "TwoEC2"
        (vpc, pubSubnet, priSubnet) = self.defineNetworkStuff(tn, tn)
        # sn_public = self.defineSubnet("PublicOneEC2",vpc, tn, public=True,  )
        ec2_1_sec_grp = self.defineSecurityGroup("EC2_2_Instance_SG", vpc, tn)
        ec2_public = self.defineEC2Instance("PublicTwoEC2Instance1", vpc, pubSubnet, ec2_1_sec_grp, tn)
        ec2_public2 = self.defineEC2Instance("PublicTwoEC2Instance2", vpc, pubSubnet, ec2_1_sec_grp, tn)
        tags.of(ec2_public).add("Product", "B")
        tags.of(ec2_public2).add("Product", "B")
        tags.of(ec2_public).add("Patch Group", "B")
        tags.of(ec2_public2).add("Patch Group", "B")
        tags.of(ec2_public).add("SSMManager", "True")
        tags.of(ec2_public2).add("SSMManager", "True")

    def installOneEC2(self):
        tn = "OneEC2"
        (vpc, pubSubnet, priSubnet) = self.defineNetworkStuff(tn, tn)
        # sn_public = self.defineSubnet("PublicOneEC2",vpc, tn, public=True,  )
        ec2_1_sec_grp = self.defineSecurityGroup("EC2_1_Instance_SG", vpc, "OneEC2")
        ec2_public = self.defineEC2Instance("PublicOneEC2Instance", vpc, pubSubnet, ec2_1_sec_grp, tn)
        tags.of(ec2_public).add("Patch Group", "Blue")
        tags.of(ec2_public).add("SSMManager", "True")

    def maz2EC2(self):
        tn = "MAZ-2EC2"
        (vpc, pubSubnet, priSubnet) = self.defineNetworkStuff(tn, tn)
        # sn_public = self.defineSubnet(f"{tn}PublicOneEC2",vpc, tn, public=True,  )
        ec2_1_sec_grp = self.defineSecurityGroup(f"{tn}_Instance_SG", vpc, tn)
        self.defineASGLoadBalancer(tn, ec2_1_sec_grp, vpc, pubSubnet, priSubnet, tn)
        tags.of(ec2_1_sec_grp).add("Product", "Red")

    def EC2ResilienceCheckingResources(self, vpc, pubSubnet, priSubnet):
        #       self.installOneEC2()
        self.twoEC2()
        #       self.maz2EC2()
        tn = "ECS-3EC2"
        #       (vpc, pubSubnet, priSubnet) = self.defineNetworkStuff(tn, tn)
        # sn_public = self.defineSubnet(f"{tn}PublicOneEC2",vpc, tn, public=True,  )
        ec2_1_sec_grp = self.defineSecurityGroup(f"{tn}MAZ_2EC2_Instance_SG", vpc, tn)
        asg = self.defineASGLoadBalancer(tn, ec2_1_sec_grp, vpc, pubSubnet, priSubnet, tn)
        subnetList = [pubSubnet, priSubnet]
        return asg, subnetList, tn, vpc

    def createECSec2Cluster(self, name, vpc, desired_cnt, min, max, tag, container_insights=False):
        cluster = ecs.Cluster(self, f"ECSCluster-{name}", cluster_name=name, vpc=vpc, container_insights=container_insights)
        cluster.add_capacity(f"ECS-ScalingCapacity-{name}", instance_type=ec2.InstanceType("t2.xlarge"),
                             desired_capacity=desired_cnt, min_capacity=min, max_capacity=max)
        ecsCluster = ecsp.ApplicationLoadBalancedEc2Service(self, name,
                                                            task_image_options=ecsp.ApplicationLoadBalancedTaskImageOptions(
                                                                image=ecs.ContainerImage.from_registry(
                                                                    "amazon/amazon-ecs-sample")),
                                                            memory_limit_mib=1024,
                                                            public_load_balancer=True,
                                                            desired_count=desired_cnt,
                                                            cluster=cluster

                                                            )
        tags.of(ecsCluster).add("Product", tag)
        tags.of(cluster).add("Product", tag)

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # EC2 Related Checks
        #        asg, subnetList, tn, vpc = self.EC2ResilienceCheckingResources()

        # ECS Setup
        # TODO Make the S3 bucket available to installer
        tn = 'Network1'
        (vpc, pubSubnet, priSubnet) = self.defineNetworkStuff(tn, tn)
        # cluster = self.defineECScluster(tn, vpc, subnetList, asg, tn)
        # RDS Checks
        dbNoMultiAZ = self.defineRDSMySQLNoMultiAz("RDSMySQLNoMultiAZ", vpc=vpc)
        dbMultiAZ = self.defineRDSMySQLMultiAz("RDSMySQLMultiAZ",vpc=vpc)

        # Kinesis Checks
        kinesisSingleShard = self.defineKinesisOneShard("KinesisOneShard")
        kinesisMultiShard = self.defineKinesisMultiShard("KinesisMultiShard")

        # ECS Cluster
        self.createECSec2Cluster("ECSMinSize", vpc=vpc, desired_cnt=1, min=0, max=1, tag="Red", container_insights=False, )
        self.createECSec2Cluster("ECSNoSpread", vpc=vpc, desired_cnt=2, min=1, max=3, tag="Red", container_insights=True)
        self.createECSec2Cluster("ECSAllOk", vpc=vpc, desired_cnt=2, min=2, max=3, tag="Blue",
                                 container_insights=True)
