import os
import json
import string
import boto3
import hashlib

with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()
with open("/var/openfaas/secrets/aws-s3-partial", "r") as f:
    AWS_S3_Partial=f.read()
s3_client = boto3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)

def handle(req):
    event = req.split(",")
    s3_client.download_file(AWS_S3_Full, "original/" + event[0], "/tmp/temp")
    with open("/tmp/temp", "rb") as check:
        data = check.read()
        md5 = hashlib.md5(data).hexdigest()
    if event[1] == md5:
        s3_client.upload_file("/tmp/temp", AWS_S3_Full, "checksumed/"+event[0])
        return "success"
    return "failed"
