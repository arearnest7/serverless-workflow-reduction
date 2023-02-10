import requests
import json
import boto3
import pprint
import csv
import os

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

#initialize
pp = pprint.PrettyPrinter(indent=4)
s3 = boto3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)
client = boto3.client('comprehend', region_name='us-west-2', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)

def db_handler(req):
    '''
    Adds the review data to the review database table
    '''
    
    event = req
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
        
    return response


def sfail_handler(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    return "SentimentFail: Fail: \"Sentiment Analysis Failed!\""

def sns_handler(req):
    event = req
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
        'feedback': event['feedback'],
    })

def service_result_handler(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    
    event = req
    results = ""
    if event["sentiment"] == "POSITIVE" or event["sentiment"] == "NEUTRAL":
        results = db_handler(event)
    elif event["sentiment"] == "NEGATIVE":
        results = sns_handler(event)
    else:
        results = sfail_handler(event)

    return results

def product_result_handler(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    
    event = req
    results = ""
    if event["sentiment"] == "POSITIVE" or event["sentiment"] == "NEUTRAL":
        results = db_handler(event)
    elif event["sentiment"] == "NEGATIVE":
        results = sns_handler(event)
    else:
        results = sfail_handler(event)

    return results

def cfail_handler(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    return "CategorizationFail: Fail: \"Input CSV could not be categorised into 'Product' or 'Service'.\""


def product_sentiment_handler(req):
    event = req
    '''
    perform sentiment analysis on the input feedback
    '''
    
    #use comprehend to perform sentiment analysis
    feedback = event['feedback']
    sentiment=client.detect_sentiment(Text=feedback,LanguageCode='en')['Sentiment']
    
    #pass through values
    return product_result_handler({
        'sentiment': sentiment,
        'reviewType': event['reviewType'],
        'reviewID': event['reviewID'],
        'customerID': event['customerID'],
        'productID': event['productID'],
        'feedback': event['feedback'],
    })

def service_sentiment_handler(req):
    event = req
    '''
    perform sentiment analysis on the input feedback
    '''
    #use comprehend to perform sentiment analysis
    feedback = event['feedback']
    sentiment=client.detect_sentiment(Text=feedback,LanguageCode='en')['Sentiment']
    
    #pass through values
    return service_result_handler({
        'sentiment': sentiment,
        'reviewType': event['reviewType'],
        'reviewID': event['reviewID'],
        'customerID': event['customerID'],
        'productID': event['productID'],
        'feedback': event['feedback'],
    })

def product_or_service_handler(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    event = req
    results = ""
    if event["reviewType"] == "Product":
        results = product_sentiment_handler(event)
    elif event["reviewType"] == "Service":
        results = service_sentiment_handler(event)
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
