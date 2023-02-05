import requests
import json
import boto3

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"
with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()
with open("/var/openfaas/secrets/aws-sns", "r") as f:
    AWS_SNS=f.read()
with open("/var/openfaas/secrets/aws-products-db", "r") as f:
    AWS_Products_DB=f.read()
with open("/var/openfaas/secrets/aws-services-db", "r") as f:
    AWS_Services_DB=f.read()

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

def sns_handler(req):
    event = json.loads(req)
    '''
    Sends notification of negative results from sentiment analysis via SNS
    '''
    
    #construct message from input data and publish via SNS
    sns = boto3.client('sns', region_name='us-west-2', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)
    sns.publish(
        TopicArn = AWS_SNS,
        Subject = 'Negative Review Received',
        Message = 'Review (ID = %i) of %s (ID = %i) received with negative results from sentiment analysis. Feedback from Customer (ID = %i): "%s"' % (int(event['reviewID']), 
                    event['reviewType'], int(event['productID']), int(event['customerID']), event['feedback'])
    )
    
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
