import boto3
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"
with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()
with open("/var/openfaas/secrets/aws-s3-partial", "r") as f:
    AWS_S3_Partial=f.read()

s3 = boto3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)

def handle(req):
    manifest = s3.list_objects(Bucket=AWS_S3_Partial, Prefix="raw/")

    total = {'statistics': {'total': 0, 'staff-number': 0, 'teamleader-number': 0, 'manager-number': 0}}
    base = {'statistics': {'staff': 0, 'teamleader': 0, 'manager': 0}}
    merit = {'statistics': {'staff': 0, 'teamleader': 0, 'manager': 0}}

    for obj in manifest["Contents"]:
        if obj["Key"] != "raw/":
            s3.download_file(AWS_S3_Partial, obj["Key"], "/tmp/temp")
            doc = {}
            with open("/tmp/temp", "r") as f:
                doc = json.load(f)
                total['statistics']['total'] += doc['total']
                total['statistics'][doc['role']+'-number'] += 1
                base['statistics'][doc['role']] += doc['base']
                merit['statistics'][doc['role']] += doc['merit']

    fs = []
    with ThreadPoolExecutor(max_workers=len(manifest["Contents"])) as executor:
        for obj in manifest["Contents"]:
            if obj["Key"] != "raw/":
                fs.append(executor.submit(requests.get, url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/partial-wage-sum-avg-merit-write', data = json.dumps({'total': total, 'base': base, 'merit': merit, 'operator': obj["Key"]})))
    results = [f for f in fs]
    return "processed batch at " + str(time.time())
