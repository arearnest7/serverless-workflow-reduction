import os
import json
import string
import boto3
from cryptography.fernet import Fernet

with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()
with open("/var/openfaas/secrets/aws-s3-partial", "r") as f:
    AWS_S3_Partial=f.read()
s3_client = boto3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)

def handle(req):
    event = req.split(",")
    s3_client.download_file(AWS_S3_Full, "ziped/" + event[0] + ".zip", "/tmp/temp.zip")
    key = Fernet.generate_key()
    with open('/tmp/temp.key', 'wb') as filekey:
        filekey.write(key)
    filekey.close()
    fernet = Fernet(key)
    data = ""
    with open("/tmp/temp.zip", "rb") as file:
        data = file.read()
    file.close()
    encrypted_data = fernet.encrypt(data)
    with open("/tmp/temp.zip", "wb") as file:
        file.write(encrypted_data)
    file.close()
    s3_client.upload_file("/tmp/temp.zip", AWS_S3_Full, "encrypted/"+event[0]+".zip")
    s3_client.upload_file("/tmp/temp.key", AWS_S3_Full, "encrypted/"+event[0]+".key")
    return "success"
