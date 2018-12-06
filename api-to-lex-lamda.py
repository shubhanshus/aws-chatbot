import os
import json
import boto3


def lambda_handler(event, context):
    
    
    print ("in here",json.dumps(event))
    message = event['params']['message']
    # print (message)
    client = boto3.client('lex-runtime', region_name = 'us-east-1')
    response = client.post_text(
    botName='foodorder',
    botAlias='foodorder',
    userId = event['params']['userId'],
    sessionAttributes={
    },
    requestAttributes={
    },
    inputText=message
    )
    
    messageReply = response['message']
     
    data =  {
                "response": messageReply
            }
    response = {
        'statusCode': 200,
        'headers': { 'Content-Type': 'application/json', "Access-Control-Allow-Origin": "*" },
        'body': data
    }
    
    
    return response