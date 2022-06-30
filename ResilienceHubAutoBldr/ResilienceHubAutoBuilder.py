import boto3
import argparse
import json


class ResilienceHubAutoBuilder:
    productTagKey = None
    productTagValue = None
    publishOnCreate = False
    assessOnCreate = False
    parser = None

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Autobuild a Resilience Hub Application for a given resource tag group.\n Verion=0.1')
        self.parser.add_argument('--app_name', type=str, required=True,
                                 help='Specify resource tag Key nameidentifying resources defined to the Resilience Hub application')
        self.parser.add_argument('--tagKey', type=str, required=True,
                                 help='Specify resource tag Key nameidentifying resources defined to the Resilience Hub application')
        self.parser.add_argument('--tagValue', type=str, required=True,
                                 help='Specify resource tag value nameidentifying resources defined to the Resilience Hub application.  If resources already defined, will add the resources not already defined (it will not delete resources)')
        self.parser.add_argument('--policyName', type=str, required=True,
                                 help='Specify resource tag value nameidentifying resources defined to the Resilience Hub application.  If resources already defined, will add the resources not already defined (it will not delete resources)')
        self.parser.add_argument("--publish",
                                 help="(Optional) Select to immediately publish Resiliency Hub application after creation",
                                 action="store_true")
        self.parser.add_argument("--assess",
                                 help="(Optional) Select to immediately begin assessing the Resilience Hub Application",
                                 action="store_true")

    def deleteResourceGroup(self, group_name):
        client = boto3.client('resource-groups')
        response = client.delete_group(GroupName=group_name)
        return(response)

    # TODO is this step really necessary and how do we update the resource list?
    def createResourceGroup(self, app_name, tag_key, tag_value):
        client = boto3.client('resource-groups')

        query = {
            "ResourceTypeFilters": ["AWS::AllSupported"],
            "TagFilters": [{
                "Key": tag_key,
                "Values": [tag_value]
            }]
        }
        resource_query = {
            'Type': 'TAG_FILTERS_1_0',
            'Query': json.dumps(query)
        }
        kwargs = {
            'Name': app_name,
            'Description': 'AWS resources assigned to the foo cluster.',
            'ResourceQuery': resource_query,
            'Tags': {
                tag_key: tag_value
            }
        }

        response = client.create_group(**kwargs)
        return (response['Group'])


    def getPolicy(self, policy_name):
        """
        Gets the JSON Policy definition for the first occurrence of policy name
        :param policy_name:
        :return:
        """
        client = boto3.client('resiliencehub')
        policies = client.list_resiliency_policies(policyName=policy_name)
        result = []
        if policies is not None and len(policies['resiliencyPolicies']) > 0:
            result = policies['resiliencyPolicies'][0]
        return(result)

    def getPolicyArn(self, policy_name):
        policy = self.getPolicy(policy_name)
        return(policy['policyArn'])

    def getResourceGroupArn(self, res_group_name):
        client = boto3.client("resource-groups")
        group_members = client.get_group(Group=res_group_name)
        groupArn = group_members['Group']['GroupArn']
        print(groupArn)
        return(groupArn)


    def getResourceGroupMembers(self, res_group_name):
        client = boto3.client("resource-groups")
        group_members = client.list_group_resources(Group=res_group_name)
        result = []
        if len(group_members['Resources']) > 0:
            for r in group_members['Resources']:
                arn = r['Identifier']['ResourceArn']
                print(arn)
                result.append(arn)

        return(result)

    # TODO Include assumptions in the README.md
    def createApp(self, app_name, res_group_name, policy_name, tagKey, tagValue, publishOnCreate=False,
                  assessOnCreate=False):
        client = boto3.client('resiliencehub')
        policyArn = self.getPolicyArn(policy_name)
        #resource_group_members = self.getResourceGroupMembers(res_group_name)
        resource_group_arn = self.getResourceGroupArn(res_group_name)
        app = client.create_app(
                                clientToken=app_name,
                                name=app_name,
                                policyArn=policyArn,
                                tags={
                                    tagKey: tagValue
                                })


        client.import_resources_to_draft_app_version(
            appArn=app['app']['appArn'],
            sourceArns=[resource_group_arn]
        )
        return(app)

    def publishApp(self, app_name):
        return (None)

    def assessApp(self, app_name, assessmentName):
        return (None)


if __name__ == "__main__":
    r = ResilienceHubAutoBuilder()
    args = r.parser.parse_args()
    if args.verbose:
        # TODO output the parameters and describe what is getting done
        print("Doing something")
    res_group = r.createResourceGroup(args.app_name, args.tagKey, args.tagValue)
    result = r.createApp(args.app_name, res_group, args.policyName, args.tagKey, args.tagVale, args.publish,
                         args.assess)
    print(result)
    if args.verbose:
        # TODO described what happened
        print(result)
