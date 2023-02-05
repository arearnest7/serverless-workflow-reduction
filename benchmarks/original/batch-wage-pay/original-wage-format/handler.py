import requests
import json

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

TAX = 0.0387
INSURANCE = 1500

def handle(req):
    params = json.loads(req)
    print(type(params))
    params['INSURANCE'] = INSURANCE

    total = INSURANCE + params['base'] + params['merit']
    params['total'] = total

    realpay = (1-TAX) * (params['base'] + params['merit'])
    params['realpay'] = realpay

    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-wage-write-raw', data = json.dumps(params))
    return response.text
