import requests
import json
import os
import sys
import redis

TAX = 0.0387
INSURANCE = 1500
ROLES = ['staff', 'teamleader', 'manager']
OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

with open('/var/openfaas/secrets/redis-password', 'r') as s:
    redisPassword = s.read()
redisHostname = os.getenv('redis_hostname')
redisPort = os.getenv('redis_port')
redisClient = redis.Redis(
                host=redisHostname,
                port=redisPort,
                password=redisPassword,
            )

def write_raw_handler(req):
    params = json.loads(req)
    #with open("/tmp/temp", "w") as f:
    #    f.write(req)
    #f.close()
    #s3.upload_file("/tmp/temp", AWS_S3_Partial, "raw/" + str(params["id"]))
    redisClient.set("raw-" + str(params["id"]), req)
    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/partial-wage-stats', data = json.dumps(req))
    return response.text

def format_handler(req):
    params = json.loads(req)
    params['INSURANCE'] = INSURANCE

    total = INSURANCE + params['base'] + params['merit']
    params['total'] = total

    realpay = (1-TAX) * (params['base'] + params['merit'])
    params['realpay'] = realpay

    return write_raw_handler(json.dumps(params))

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
    return format_handler(req)
