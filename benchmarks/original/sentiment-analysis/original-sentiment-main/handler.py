import requests
import json
import boto3
import pprint

#initialize
OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"
pp = pprint.PrettyPrinter(indent=4)

def handle(req):
    '''
    triggers a step function from the S3 landing event, 
    passing along the S3 file info
    '''
    
    event = json.loads(req)
    #Fallback tests for initializations outside scope
    try:
        pp
    except NameError:
        pp = pprint.PrettyPrinter(indent=4)

    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = event['Records'][0]['s3']['object']['key']

    
    input= {
            'bucket_name': bucket_name,
            'file_key': file_key
        }
        
    #stepFunction = boto3.client('stepfunctions')
    #response = stepFunction.start_execution(
    #    stateMachineArn='arn:aws:states:XXXXXXXXXXXXXXXX:stateMachine:my-state-machine',
    #    input = json.dumps(input, indent=4)
    #)
    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-sentiment-read-csv', data = json.dumps(input))
    
    return response.text
