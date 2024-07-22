import boto3
import os

AGENT_ID = "HTWBIU7STM"
AGENT_ALIAS = "ENXLBWQ7TZ"

def invoke_llm(input, userID):
    bedrock = boto3.client(
        service_name='bedrock-agent-runtime', 
        region_name='us-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            
    )   
    bedrockObj = bedrock.invoke_agent (
        agentAliasId=AGENT_ALIAS,
        agentId=AGENT_ID,
        inputText=input,
        sessionId=userID
    )

    for event in bedrockObj['completion']:
        data = event['chunk']['bytes'].decode('utf-8')
    
    return data
    
if __name__ == "__main__":
    msg = input("Enter a message: ")
    id = input("Enter a session ID: ")
    print(invoke_llm(msg, id))