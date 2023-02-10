import boto3
import requests
import json

TAX = 0.0387
INSURANCE = 1500
ROLES = ['staff', 'teamleader', 'manager']
OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"
with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()
with open("/var/openfaas/secrets/aws-s3-partial", "r") as f:
    AWS_S3_Partial=f.read()

s3 = boto3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)

def write_raw_handler(req):
    data = json.loads(req)
    with open("/tmp/temp", "w") as f:
        f.write(req)
    s3.upload_file("/tmp/temp", AWS_S3_Partial, "raw/" + str(params["id"]))
    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/partial-wage-stats', data = json.dumps(req))
    return response.text

def format_handler(req):
    data = json.loads(req)
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
