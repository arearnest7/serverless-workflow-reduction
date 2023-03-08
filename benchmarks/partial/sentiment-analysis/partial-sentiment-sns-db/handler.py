import requests
import json
import os
import sys
from pymongo import MongoClient
from urllib.parse import quote_plus

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

with open("/var/openfaas/secrets/mongo-db-password") as f:
    password = f.read()

def sfail_handler(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    return "SentimentFail: Fail: \"Sentiment Analysis Failed!\""

def db_handler(req):
    '''
    Adds the review data to the review database table
    '''
    
    event = req
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

def sns_handler(req):
    event = req
    '''
    Sends notification of negative results from sentiment analysis via SNS
    '''
    
    #construct message from input data and publish via SNS
    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/shasum' , data = json.dumps({
        "Subject": 'Negative Review Received',
        "Message": 'Review (ID = %i) of %s (ID = %i) received with negative results from sentiment analysis. Feedback from Customer (ID = %i): "%s"' % (int(event['reviewID']),
        event['reviewType'], int(event['productID']), int(event['customerID']), event['feedback'])
    }))
    
    #pass through values
    return db_handler({
        'sentiment': event['sentiment'],
        'reviewType': event['reviewType'],
        'reviewID': event['reviewID'],
        'customerID': event['customerID'],
        'productID': event['productID'],
        'feedback': event['feedback']
    })

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    event = json.loads(req)
    results = ""
    if event["sentiment"] == "POSITIVE" or event["sentiment"] == "NEUTRAL":
        results = db_handler(event)
    elif event["sentiment"] == "NEGATIVE":
        results = sns_handler(event)
    else:
        results = sfail_handler(event)

    return results
