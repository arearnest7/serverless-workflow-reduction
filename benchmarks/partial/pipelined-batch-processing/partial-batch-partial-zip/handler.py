from zipfile import ZipFile
import os
import json
import string
import boto3

with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()
with open("/var/openfaas/secrets/aws-s3-partial", "r") as f:
    AWS_S3_Partial=f.read()
s3_client = boto3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)

def handle(req):
    event = req.split(",")
    s3_client.download_file(AWS_S3_Full, "checksumed/" + event[0] , "/tmp/temp")
    with ZipFile('/tmp/temp.zip', 'w') as zip:
        zip.write("/tmp/temp")
    zip.close()
    s3_client.upload_file("/tmp/temp.zip", AWS_S3_Full, "ziped/"+event[0]+".zip")
    return "success"
