import requests
import json

ROLES = ['staff', 'teamleader', 'manager']
OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

def handle(req):
    event = json.loads(req)
    for param in ['id', 'name', 'role', 'base', 'merit', 'operator']:
        if param in ['name', 'role']:
            if not isinstance(event[param], str):
                return "fail: illegal params: " + str(event[param]) + " not string"
            elif param == 'role' and event[param] not in ROLES:
                return "fail: invalid role: " + str(event[param])
        elif param in ['id', 'operator']:
            if not isinstance(event[param], int):
                return "fail: illegal params: " + str(event[param]) + " not integer"
        elif param in ['base', 'merit']:
            if not isinstance(event[param], float):
                return "fail: illegal params: " + str(event[param]) + " not float"
            elif event[param] < 1 or event[param] > 8:
                return "fail: illegal params: " + str(event[param]) + " not between 1 and 8 inclusively"
        else:
            return "fail: missing param: " + param
    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-wage-format', data = json.dumps(req))
    return response.text
