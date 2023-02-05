import requests
import json
import boto3

with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()
with open("/var/openfaas/secrets/aws-products-db", "r") as f:
    AWS_Products_DB=f.read()
with open("/var/openfaas/secrets/aws-services-db", "r") as f:
    AWS_Services_DB=f.read()

def handle(req):
    '''
    Adds the review data to the review database table
    '''
    
    event = json.loads(req)
    #select correct table based on input data
    dynamodb = boto3.client('dynamodb', region_name='us-west-2', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)
    if event['reviewType'] == 'Product':
        tableName = AWS_Products_DB
    elif event['reviewType'] == 'Service':
        tableName = AWS_Services_DB
    else:
        raise Exception("Input review is neither Product nor Service")
    
    #construct response to put data in table
    response = dynamodb.put_item(
        TableName=tableName,
        Item={
            'reviewID': {"N": event['reviewID'] },
            'customerID': {"N": event['customerID'] },
            'productID': {"N": event['productID'] },
            'feedback': {"S": event['feedback'] },
            'sentiment': {"S": event['sentiment'] }
        },
    )
    
    #pass through values 
    response['reviewType'] = event['reviewType']
    response['reviewID'] = event['reviewID']
    response['customerID'] = event['customerID']
    response['productID'] = event['productID']
    response['feedback'] = event['feedback']
    response['sentiment'] = event['sentiment']
        
    return json.dumps(response)
