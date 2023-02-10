import requests
import json
import boto3
import pprint
import csv
import os

#initialize
OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"
with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()

pp = pprint.PrettyPrinter(indent=4)
s3 = boto3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)

def cfail_handler(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    return "CategorizationFail: Fail: \"Input CSV could not be categorised into 'Product' or 'Service'.\""

def product_or_service_handler(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    event = req

    results = ""
    if event["reviewType"] == "Product":
        response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/partial-sentiment-product-path' , data = json.dumps(event))
        results = response.text
    elif event["reviewType"] == "Service":
        response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/partial-sentiment-service-path' , data = json.dumps(event))
        results = response.text
    else:
        results = cfail_handler(event)
    return results

def read_csv_handler(req):
    '''
    reads the .csv from the S3 landing event, returns a json-formatted
    dict formed from the first line (and column headers)
    '''
    
    #Fallback tests for initializations outside scope
    event = req
    try:
        s3
    except NameError:
        s3 = boto3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)
    
    
    #read s3 object
    bucket_name = event['bucket_name']
    file_key = event['file_key']
    response = s3.get_object(Bucket=bucket_name, Key=file_key)
    
    #convert response to lines of CSV
    lines = response['Body'].read().decode('utf-8').split('\n')
    
    #DictReader -> convert lines of CSV to OrderedDict
    for row in csv.DictReader(lines):
        #return just the first loop (row) results!
        return product_or_service_handler(row)

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
    response = read_csv_handler(input)
    
    return response
