import requests
import os
import json

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

def handle(req):
    event = json.loads(req)

    '''
    perform sentiment analysis on the input feedback
    '''
    
    #use comprehend to perform sentiment analysis
    feedback = event['feedback']
    #sentiment=client.detect_sentiment(Text=feedback,LanguageCode='en')['Sentiment']
    response = json.loads(requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/sentimentanalysis' , data = feedback).text)
    if response['polarity'] > 0.5:
        sentiment = "POSITIVE"
    elif response['polarity'] < -0.5:
        sentiment = "NEGATIVE"
    else:
        sentiment = "NEUTRAL"
    
    #pass through values
    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-sentiment-product-result' , data = json.dumps({
        'sentiment': sentiment,
        'reviewType': event['reviewType'],
        'reviewID': event['reviewID'],
        'customerID': event['customerID'],
        'productID': event['productID'],
        'feedback': event['feedback']
    }))
    return response.text
