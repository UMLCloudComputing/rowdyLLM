import boto3
import os
from dotenv import load_dotenv
import json
from botocore.exceptions import ClientError
from logging import *
import random
import string
import time

load_dotenv()

AWS_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Prompts
prompt = '''System: A chat between a curious User and an artificial intelligence Bot. The Bot gives helpful, detailed, and polite answers to the User's questions. In this session, the model has access to external functionalities.
To assist the user, you can reply to the user or invoke an action. Only invoke actions if relevant to the user request.
$instruction$

The following actions are available:$tools$
Model Instructions:
$model_instructions$
$conversation_history$
User: $question$
$thought$ $bot_response$
'''

kbgeneration = '''A chat between a curious User and an artificial intelligence Bot. The Bot gives helpful, detailed, and polite answers to the User's questions.

In this session, the model has access to search results and a user's question, your job is to answer the user's question using only information from the search results.

Model Instructions:
- You should provide concise answer to simple questions when the answer is directly contained in search results, but when comes to yes/no question, provide some details.
- In case the question requires multi-hop reasoning, you should find relevant information from search results and summarize the answer based on relevant information with logical reasoning.
- If the search results do not contain information that can answer the question, please state that you could not find an exact answer to the question, and if search results are completely irrelevant, say that you could not find an exact answer, then summarize search results.
- Remember to add a citation to the end of your response using markers like %[1]%, %[2]%, %[3]%, etc for the corresponding passage supports the response.
- DO NOT USE INFORMATION THAT IS NOT IN SEARCH RESULTS!

User: $query$ Bot:
Resources: Search Results: $search_results$ Bot:
'''

with open('instructions.txt', 'r') as file:
    # Step 2: Read the contents
    instruction = file.read()

bedrock = boto3.client(
    service_name='bedrock-agent', 
    region_name='us-east-1',
    aws_access_key_id=AWS_ID,
    aws_secret_access_key=AWS_KEY
)

def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

# random_string = generate_random_string(10)
# print(random_string)

def create_agent_role(model_id, policy_name):
    role_name = f"AmazonBedrockExecutionRoleForAgents_{generate_random_string(10)}"
    model_arn = f"arn:aws:bedrock:us-east-1::foundation-model/{model_id}*"

    print("Creating an an execution role for the agent...")

    iam_resource=boto3.resource(
        service_name="iam",
        region_name='us-east-1',
        aws_access_key_id=AWS_ID,
        aws_secret_access_key=AWS_KEY           
    )

    try:
        role = iam_resource.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "bedrock.amazonaws.com"},
                            "Action": "sts:AssumeRole",
                        }
                    ],
                }
            ),
        )

        role.Policy(policy_name).put(
            PolicyDocument=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "bedrock:InvokeModel",
                            "Resource": model_arn,
                        },
                        {
                            "Effect": "Allow",
                            "Action": "bedrock:ListAgentAliases",
                            "Resource": "*"
                        }
                    ],
                }
            )
        )
    except ClientError as e:
        print(f"Couldn't create role {role_name}. Here's why: {e}")
        raise

    sts_client = boto3.client(
        service_name='sts', 
        region_name='us-east-1',
        aws_access_key_id=AWS_ID,
        aws_secret_access_key=AWS_KEY
    )
    
    caller_identity = sts_client.get_caller_identity()
    account_id = caller_identity['Account']

    returnStr = f"arn:aws:iam::{account_id}:role/{role_name}"
    return returnStr

# Create Amazon Bedrock Agent
def create_agent(agent_name):
    response = bedrock.create_agent(
        agentName=agent_name,
        agentResourceRoleArn=create_agent_role('amazon.titan-text-premier-v1:0', 'AmazonBedrockExecutionRoleForAgents'),
        description='Testing',
        foundationModel='amazon.titan-text-premier-v1:0',
        idleSessionTTLInSeconds=123,
        instruction=instruction,
        promptOverrideConfiguration={
            'promptConfigurations': [
                {
                    'basePromptTemplate': prompt,
                    'inferenceConfiguration': {
                        'maximumLength': 256,
                        'temperature': 0, 
                        'topK': 123,
                        'topP': 0.1
                    },
                    'parserMode': 'DEFAULT',
                    'promptCreationMode': 'OVERRIDDEN',
                    'promptState': 'ENABLED',
                    'promptType': 'ORCHESTRATION'
                },

                {
                    'basePromptTemplate': prompt,
                    'inferenceConfiguration': {
                        'maximumLength': 256,
                        'temperature': 0,
                        'topK': 123,
                        'topP': 0.1
                    },
                    'parserMode': 'DEFAULT',
                    'promptCreationMode': 'OVERRIDDEN',
                    'promptState': 'ENABLED',
                    'promptType': 'KNOWLEDGE_BASE_RESPONSE_GENERATION'
                }
            ]
        },
        tags={
            'string': 'string'
        }
    )

    time.sleep(5)
    prepare_agent(response['agent']['agentId'])

    time.sleep(3)
    alias_response = create_alias(response['agent']['agentId'], f"{agent_name}_alias")

    # Add AGENT_ID = response['agent']['agentId'] to .env file. If the files doesn't exit create one
    write_agent_id(response['agent']['agentId'])
    write_agent_alias(alias_response['agentAlias']['agentAliasId'])

    return f"Agent Information: https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/agents/{response['agent']['agentId']}/"

def write_agent_id(agent_id):
    env_path = '.env'
    agent_id_line = f"AGENT_ID = {agent_id}\n"
    try:
        with open(env_path, 'r') as file:
            lines = file.readlines()
        
        with open(env_path, 'w') as file:
            agent_id_found = False
            for line in lines:
                if line.startswith('AGENT_ID'):
                    file.write(agent_id_line)
                    agent_id_found = True
                else:
                    file.write(line)
            if not agent_id_found:
                file.write(agent_id_line)
    except FileNotFoundError:
        with open(env_path, 'w') as file:
            file.write(agent_id_line)

def write_agent_alias(agent_id):
    env_path = '.env'
    agent_id_line = f"AGENT_ALIAS = {agent_id}\n"
    try:
        with open(env_path, 'r') as file:
            lines = file.readlines()
        
        with open(env_path, 'w') as file:
            agent_id_found = False
            for line in lines:
                if line.startswith('AGENT_ALIAS'):
                    file.write(agent_id_line)
                    agent_id_found = True
                else:
                    file.write(line)
            if not agent_id_found:
                file.write(agent_id_line)
    except FileNotFoundError:
        with open(env_path, 'w') as file:
            file.write(agent_id_line)

def list_agents():
    response = bedrock.list_agents(
        maxResults=123,
    )

    for summary in response['agentSummaries']:
        print(f"Agent Name: {summary['agentName']}, Agent ID: {summary['agentId']}")

def prepare_agent(agent_id):

    preparation = bedrock.prepare_agent(
        agentId=agent_id
    )

def update_agent(agent_id, agent_name):

    ARN = response = bedrock.get_agent(agentId=agent_id).get('agent').get('agentResourceRoleArn')

    response = bedrock.update_agent(
        agentId=agent_id,
        agentName=agent_name,
        agentResourceRoleArn=ARN,
        description='Testing',
        foundationModel='amazon.titan-text-premier-v1:0',
        idleSessionTTLInSeconds=123,
        instruction=instruction,
        promptOverrideConfiguration={
            'promptConfigurations': [
                {
                    'basePromptTemplate': prompt,
                    'inferenceConfiguration': {
                        'maximumLength': 256,
                        'temperature': 0, 
                        'topK': 123,
                        'topP': 0.1
                    },
                    'parserMode': 'DEFAULT',
                    'promptCreationMode': 'OVERRIDDEN',
                    'promptState': 'ENABLED',
                    'promptType': 'ORCHESTRATION'
                },

                {
                    'basePromptTemplate': prompt,
                    'inferenceConfiguration': {
                        'maximumLength': 256,
                        'temperature': 0,
                        'topK': 123,
                        'topP': 0.1
                    },
                    'parserMode': 'DEFAULT',
                    'promptCreationMode': 'OVERRIDDEN',
                    'promptState': 'ENABLED',
                    'promptType': 'KNOWLEDGE_BASE_RESPONSE_GENERATION'
                }
            ]
        },
    )


def delete_agent():
    list_agents()

    agent_id = input("Enter the agent ID you want to delete: ")

    response = bedrock.delete_agent(
        agentId=agent_id,
        skipResourceInUseCheck=True
    )

def list_agent_aliases(agentId):
    response = bedrock.list_agent_aliases(
        agentId=agentId,
        maxResults=123
    )

    for summary in response['agentAliasSummaries']:
        print(f"Alias Name: {summary['agentAliasName']}, Alias ID: {summary['agentAliasId']}")

def create_alias(agentId, alias_name):
    response = bedrock.create_agent_alias(
        agentAliasName=alias_name,
        agentId=agentId,
        description='Automatic CI/CD Alias'
    )

    return response

def update_alias(agent_alias_id, agent_id):
    response = bedrock.get_agent_alias(
        agentAliasId=agent_alias_id,
        agentId=agent_id
    )

    # version = response = bedrock.get_agent(agentId=agent_id).get('agent').get('agentVersion')
    # print(version)

    update_response = bedrock.update_agent_alias (
        agentAliasId=agent_alias_id,
        agentAliasName=response['agentAlias']['agentAliasName'],
        agentId=agent_id
    )

# if __name__ == "__main__":
#     update_alias('D4SKTGD7AO', 'P7XE1HDAQG')

    