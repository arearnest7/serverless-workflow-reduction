from zipfile import ZipFile
import os
import json
import string
import boto3

with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()
with open("/var/openfaas/secrets/aws-s3-original", "r") as f:
    AWS_S3_Original=f.read()
s3_client = boto3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)

def handle(req):
    event = req.split(",")
    s3_client.download_file(AWS_S3_Original, "checksumed/" + event[0] , "/tmp/" + event[0])
    with ZipFile('/tmp/zip.zip', 'w') as zip:
        zip.write("/tmp/" + event[0])
    zip.close()
    s3_client.upload_file("/tmp/zip.zip", AWS_S3_Original, "ziped/"+event[0]+".zip")
    return "success"
