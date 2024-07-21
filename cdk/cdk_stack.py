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
            instruction="Your identity is Rowdy the Riverhawk. Your job is the answer questions about the University of Massachusetts Lowell",
            prompt_override_configuration=bedrock.CfnAgent.PromptOverrideConfigurationProperty(
                prompt_configurations=[bedrock.CfnAgent.PromptConfigurationProperty(
                    base_prompt_template='''System: A chat between a curious User and an artificial intelligence Bot. The Bot gives helpful, detailed, and polite answers to the User's questions. In this session, the model has access to external functionalities.
To assist the user, you can reply to the user or invoke an action. Only invoke actions if relevant to the user request.
$instruction$

The following actions are available:$tools$
Model Instructions:
$model_instructions$
$conversation_history$
User: $question$
$thought$ $bot_response$''',
                    inference_configuration=bedrock.CfnAgent.InferenceConfigurationProperty(
                        maximum_length=2048,
                        temperature=0,
                        #top_k=0.1,
                        top_p=0.1,
                    ),
                    prompt_creation_mode="OVERRIDDEN",
                    prompt_type="ORCHESTRATION"
                )],
            ),
        )