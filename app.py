#!/usr/bin/env python3
import os

import aws_cdk as cdk

from resilience_hub.resilience_hub_stack import ResilienceHubStack


app = cdk.App()
ResilienceHubStack(app, "MDDTestEnvironment",stack_name="MDDTestEnvironment",)

app.synth()
