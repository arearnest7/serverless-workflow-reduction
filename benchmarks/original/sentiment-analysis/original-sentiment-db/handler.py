import requests
import json
import sys
import os
from pymongo import MongoClient
from urllib.parse import quote_plus

with open("/var/openfaas/secrets/mongo-db-password") as f:
    password = f.read()

def handle(req):
    '''
    Adds the review data to the review database table
    '''
    
    event = json.loads(req)
    #select correct table based on input data
    #dynamodb = boto3.client('dynamodb', region_name='us-west-2', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)
    #if event['reviewType'] == 'Product':
    #    tableName = AWS_Products_DB
    #elif event['reviewType'] == 'Service':
    #    tableName = AWS_Services_DB
    #else:
    #    raise Exception("Input review is neither Product nor Service")

    #construct response to put data in table
    #response = dynamodb.put_item(
    #    TableName=tableName,
    #    Item={
    #        'reviewID': {"N": event['reviewID'] },
    #        'customerID': {"N": event['customerID'] },
    #        'productID': {"N": event['productID'] },
    #        'feedback': {"S": event['feedback'] },
    #        'sentiment': {"S": event['sentiment'] }
    #    },
    #)
    client = MongoClient("mongodb://%s:%s@%s" % (quote_plus("root"), quote_plus(password), os.getenv("mongo_host")))
    db = client['openfaas']
    table = ""
    if event['reviewType'] == 'Product':
        table = db.products
    elif event['reviewType'] == 'Service':
        table = db.services
    else:
        raise Exception("Input review is neither Product nor Service")
    Item = {
       'reviewID': event['reviewID'],
        'customerID': event['customerID'],
        'productID': event['productID'],
        'feedback': event['feedback'],
        'sentiment': event['sentiment']
    }
    response = {"response": str(table.insert_one(Item).inserted_id)}

    #pass through values 
    response['reviewType'] = event['reviewType']
    response['reviewID'] = event['reviewID']
    response['customerID'] = event['customerID']
    response['productID'] = event['productID']
    response['feedback'] = event['feedback']
    response['sentiment'] = event['sentiment']
        
    return json.dumps(response)
