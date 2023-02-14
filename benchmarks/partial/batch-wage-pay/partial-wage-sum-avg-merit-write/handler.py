import boto3
import requests
import json

TAX = 0.0387
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

def write_merit_handler(req):
    params = json.loads(req)

    with open("/tmp/temp", "w") as f:
        f.write(req)
    f.close()
    s3.upload_file("/tmp/temp", AWS_S3_Partial, "merit/" + str(params["id"]))

    return str(params["id"]) + " statistics uploaded/updated"

def wage_merit_handler(req):
    params = json.loads(req)
    meritp = {'staff': 0, 'teamleader': 0, 'manager': 0}
    for role in ROLES:
        num = params['total']['statistics'][role+'-number']
        if num != 0:
            base = params['base']['statistics'][role]
            merit = params['merit']['statistics'][role]
            meritp[role] = merit / base
    params['statistics']['average-merit-percent'] = meritp
    return write_merit_handler(json.dumps({'id': params['id'], 'statistics': params['statistics'], 'operator' : params['operator']}))

def wage_avg_handler(req):
    params = json.loads(req)

    realpay = {'staff': 0, 'teamleader': 0, 'manager': 0}
    for role in ROLES:
        num = params['total']['statistics'][role+'-number']
        if num != 0:
            base = params['base']['statistics'][role]
            merit = params['merit']['statistics'][role]
            realpay[role] = (1-TAX) * (base + merit) / num
    params['statistics']['average-realpay'] = realpay

    return wage_merit_handler(json.dumps(params))

def handle(req):
    params = json.loads(req)
    s3.download_file(AWS_S3_Partial, params["operator"], "/tmp/temp")
    with open("/tmp/temp", "r") as f:
        temp = json.load(f)
        params["operator"] = temp["operator"]
        params["id"] = temp["id"]
    stats = {'total': params['total']['statistics']['total'] }
    params['statistics'] = stats

    return wage_avg_handler(json.dumps(params))
