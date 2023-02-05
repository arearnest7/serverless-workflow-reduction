import requests
import json

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    event = json.loads(req)
    results = ""
    if event["sentiment"] == "POSITIVE" or event["sentiment"] == "NEUTRAL":
        results = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-sentiment-db' , data = json.dumps(event))
    elif event["sentiment"] == "NEGATIVE":
        results = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-sentiment-sns' , data = json.dumps(event))
    else:
        results = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-sentiment-sfail' , data = json.dumps(event))

    return results.text
