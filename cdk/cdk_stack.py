from aws_cdk import (
    # Duration,
    Stack,
    aws_bedrock as bedrock,
    aws_iam as iam
)
from constructs import Construct
import string
import random

base_prompt_template='''System: A chat between a curious User and an artificial intelligence Bot. The Bot gives helpful, detailed, and polite answers to the User's questions. In this session, the model has access to external functionalities.
To assist the user, you can reply to the user or invoke an action. Only invoke actions if relevant to the user request.
$instruction$

The following actions are available:$tools$
Model Instructions:
$model_instructions$
$conversation_history$
User: $question$
$thought$ $bot_response$'''

kb_template='''A chat between a curious User and an artificial intelligence Bot. The Bot gives helpful, detailed, and polite answers to the User's questions.

In this session, the model has access to search results and a user's question, your job is to answer the user's question using only information from the search results.

Model Instructions:
- You should provide concise answer to simple questions when the answer is directly contained in search results, but when comes to yes/no question, provide some details.
- In case the question requires multi-hop reasoning, you should find relevant information from search results and summarize the answer based on relevant information with logical reasoning.
- If the search results do not contain information that can answer the question, please state that you could not find an exact answer to the question, and if search results are completely irrelevant, say that you could not find an exact answer, then summarize search results.
- Remember to add a citation to the end of your response using markers like %[1]%, %[2]%, %[3]%, etc for the corresponding passage supports the response.
- DO NOT USE INFORMATION THAT IS NOT IN SEARCH RESULTS!

User: $query$ Bot:
Resources: Search Results: $search_results$ Bot:'''

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
            instruction="You are a chatbot for the University of Massachusetts Lowell. Your goal is to answer questions to the best of your ability. Please ask the user to clarify if necessary",
            prompt_override_configuration=bedrock.CfnAgent.PromptOverrideConfigurationProperty(
                prompt_configurations=[
                    bedrock.CfnAgent.PromptConfigurationProperty(
                        base_prompt_template=base_prompt_template,
                        inference_configuration=bedrock.CfnAgent.InferenceConfigurationProperty(
                            maximum_length=2048,
                            temperature=0,
                            top_p=0.1,
                        ),
                        prompt_creation_mode="OVERRIDDEN",
                        prompt_type="ORCHESTRATION"
                    ),

                    bedrock.CfnAgent.PromptConfigurationProperty(
                        base_prompt_template=kb_template,
                        inference_configuration=bedrock.CfnAgent.InferenceConfigurationProperty(
                            maximum_length=2048,
                            temperature=0,
                            top_p=0.1,
                        ),
                        prompt_creation_mode="OVERRIDDEN",
                        prompt_type="KNOWLEDGE_BASE_RESPONSE_GENERATION"
                    )
                ],
            ),
        )