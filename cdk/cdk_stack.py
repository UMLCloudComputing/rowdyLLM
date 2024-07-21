from aws_cdk import (
    # Duration,
    Stack,
    aws_bedrock as bedrock,
    aws_iam as iam
)
from constructs import Construct
import string
import random


def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

class CdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.agent_name = kwargs.get('agent_name')
        
        cfn_role = iam.CfnRole(self, "AmazonBedrockAgentRole",
            assume_role_policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "bedrock.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            },
            policies=[
                {
                    "policyName": "AmazonBedrockAgentPolicy",
                    "policyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": "bedrock:InvokeModel",
                                "Resource": "*",
                            },
                            {
                                "Effect": "Allow",
                                "Action": "bedrock:Retrieve",
                                "Resource": "*",
                            }
                        ],
                    },
                }
            ],
            role_name=f"AmazonBedrockAgentRole_{construct_id}",
        )

        cfn_agent = bedrock.CfnAgent(self, "Agent",
            agent_name=f"MyAgent{construct_id}",
            description='Production',
            agent_resource_role_arn= cfn_role.attr_arn,
            auto_prepare=True,
            foundation_model="amazon.titan-text-premier-v1:0",
            instruction="Your identity is Rowdy the Riverhawk. Your job is the answer questions about the University of Massachusetts Lowell"
        )