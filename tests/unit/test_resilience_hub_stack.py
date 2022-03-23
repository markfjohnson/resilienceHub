import aws_cdk as core
import aws_cdk.assertions as assertions

from resilience_hub.resilience_hub_stack import ResilienceHubStack

# example tests. To run these tests, uncomment this file along with the example
# resource in resilience_hub/resilience_hub_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ResilienceHubStack(app, "resilience-hub")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
