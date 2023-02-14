import requests
import json

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

TAX = 0.0387
ROLES = ['staff', 'teamleader', 'manager']

def handle(req):
    params = json.loads(req)
    meritp = {'staff': 0, 'teamleader': 0, 'manager': 0}
    for role in ROLES:
        num = params['total']['statistics'][role+'-number']
        if num != 0:
            base = params['base']['statistics'][role]
            merit = params['merit']['statistics'][role]
            meritp[role] = merit / base
    params['statistics']['average-merit-percent'] = meritp
    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-wage-write-merit', data = json.dumps({'id': params['id'], 'statistics': params['statistics'], 'operator' : params['operator']}))
    return response.text
