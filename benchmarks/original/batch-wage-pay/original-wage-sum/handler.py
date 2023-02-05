import boto3
import requests
import json

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"
with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()
with open("/var/openfaas/secrets/aws-s3-original", "r") as f:
    AWS_S3_Original=f.read()

s3 = boto3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)

def handle(req):
    params = json.loads(req)
    s3.download_file(AWS_S3_Original, params["operator"], "/tmp/temp")
    with open("/tmp/temp", "r") as f:
        temp = json.load(f)
        params["operator"] = temp["operator"]
        params["id"] = temp["id"]
    stats = {'total': params['total']['statistics']['total'] }
    params['statistics'] = stats

    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-wage-avg', data = json.dumps(params))
    return response.text
