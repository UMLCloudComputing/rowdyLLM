import json
import llm

def handler(event, context):
    # Extract the URL path from the event object
    url_path = event.get('path', 'No path found')
    
    # Include the URL path in the response body
    response_body = {'message': llm.invoke_llm("What LLCs are there?", "123457"), 'path': url_path}
    
    return {'statusCode': 200, 'body': json.dumps(response_body)}