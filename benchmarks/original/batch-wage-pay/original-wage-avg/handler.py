import requests
import json

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

TAX = 0.0387
ROLES = ['staff', 'teamleader', 'manager']

def handle(req):
    params = json.loads(req)
    
    realpay = {'staff': 0, 'teamleader': 0, 'manager': 0}
    for role in ROLES:
        num = params['total']['statistics'][role+'-number']
        if num != 0:
            base = params['base']['statistics'][role]
            merit = params['merit']['statistics'][role]
            realpay[role] = (1-TAX) * (base + merit) / num
    params['statistics']['average-realpay'] = realpay

    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-wage-merit', data = json.dumps(params))
    return response.text
