import requests
import json

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

def handle(req):
    event = json.loads(req)
    '''
    Sends notification of negative results from sentiment analysis via SNS
    '''
    
    #construct message from input data and publish via SNS
    #sns = boto3.client('sns', region_name='us-west-2', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)
    #sns.publish(
    #    TopicArn = AWS_SNS,
    #    Subject = 'Negative Review Received',
    #    Message = 'Review (ID = %i) of %s (ID = %i) received with negative results from sentiment analysis. Feedback from Customer (ID = %i): "%s"' % (int(event['reviewID']),
    #    event['reviewType'], int(event['productID']), int(event['customerID']), event['feedback'])
    #)
    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/shasum' , data = json.dumps({
        TopicArn = AWS_SNS,
        Subject = 'Negative Review Received',
        Message = 'Review (ID = %i) of %s (ID = %i) received with negative results from sentiment analysis. Feedback from Customer (ID = %i): "%s"' % (int(event['reviewID']),
        event['reviewType'], int(event['productID']), int(event['customerID']), event['feedback'])
    }))
    
    #pass through values
    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-sentiment-db' , data = json.dumps({
        'sentiment': event['sentiment'],
        'reviewType': event['reviewType'],
        'reviewID': event['reviewID'],
        'customerID': event['customerID'],
        'productID': event['productID'],
        'feedback': event['feedback']
    }))
    return response.text
