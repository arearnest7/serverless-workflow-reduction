import requests
import boto3
import csv
import json
    
#initialize
OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"
with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()

s3 = boto3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)

def handle(req):
    '''
    reads the .csv from the S3 landing event, returns a json-formatted
    dict formed from the first line (and column headers)
    '''
    
    #Fallback tests for initializations outside scope
    event = json.loads(req)
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
        response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-sentiment-product-or-service', data = json.dumps(row))
        return response.text
