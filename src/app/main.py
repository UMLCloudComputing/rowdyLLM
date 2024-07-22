import json
import llm

def handler(event, context):
    body = json.loads(event.get('body'))

    msg = body['user_message']
    id = body['session_id']

    response = llm.invoke_llm(msg, id)
    response_body = {'message': response}
    
    return {'statusCode': 200, 'body': json.dumps(response_body)}