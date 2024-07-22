import boto3
from dotenv import load_dotenv
import os
import json
import re
load_dotenv()

AWS_ID = os.getenv('AWS_ID')
AWS_KEY = os.getenv('AWS_KEY')
AGENT_ID = os.getenv('AGENT_ID')
AGENT_ALIAS = os.getenv('AGENT_ALIAS')

# Call the Titan Premier Model (RAG Capabilities)
def invoke_llm(input, userID):
    bedrock = boto3.client(
        service_name='bedrock-agent-runtime', 
        region_name='us-east-1',
        aws_access_key_id=AWS_ID,
        aws_secret_access_key=AWS_KEY
            
    )   
    bedrockObj = bedrock.invoke_agent (
        agentAliasId=AGENT_ALIAS,
        agentId=AGENT_ID,
        inputText=input,
        sessionId=userID
    )

    print(bedrockObj)

    eventStream = bedrockObj['completion']
    url = ""

    for event in eventStream:
        print(event)
        if 'chunk' in event:
            data = event['chunk']['bytes'].decode('utf-8')
            returnString = data
        if 'attribution' in event['chunk']:
            for citations in event['chunk']['attribution']['citations']:
                for references in citations['retrievedReferences']:
                    print(f"Metadata\n{references}")
                    url = references.get('metadata').get('url')

    return f"{returnString}\nFind more information: {url}"

# def extract_filename(s3_uri):
#     # Regex pattern to match the filename at the end of the URI
#     pattern = r'[^/]+$'
#     # Search for the pattern in the URI and extract the filename
#     match = re.search(pattern, s3_uri)
#     if match:
#         return match.group()
#     else:
#         return None
    
if __name__ == "__main__":
    print(invoke_llm("What are some living learning communities I can participate in", "123456"))