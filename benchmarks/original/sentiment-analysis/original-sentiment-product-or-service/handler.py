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
    if event["reviewType"] == "Product":
        results = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-sentiment-product-sentiment', data = json.dumps(event))
    elif event["reviewType"] == "Service":
        results = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-sentiment-service-sentiment', data = json.dumps(event))
    else:
        results = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-sentiment-cfail', data = json.dumps(event))
    return results.text
