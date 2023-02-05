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
s3 = bot3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)
client = boto3.client('comprehend', region_name='us-west-2', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)

def handle(req):
    event = json.loads(req)
    '''
    perform sentiment analysis on the input feedback
    '''
    
    #use comprehend to perform sentiment analysis
    feedback = event['feedback']
    sentiment=client.detect_sentiment(Text=feedback,LanguageCode='en')['Sentiment']
    
    #pass through values
    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/partial-sentiment-sns-db' , data = json.dumps({
        'sentiment': sentiment,
        'reviewType': event['reviewType'],
        'reviewID': event['reviewID'],
        'customerID': event['customerID'],
        'productID': event['productID'],
        'feedback': event['feedback']
    }))
    return response.text
