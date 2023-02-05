import requests
import os
import json
import string
from concurrent.futures import ThreadPoolExecutor
import hashlib
from zipfile import ZipFile
from cryptography.fernet import Fernet
import boto3

with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()
with open("/var/openfaas/secrets/aws-s3-full", "r") as f:
    AWS_S3_Full=f.read()

s3_client = boto3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)

def checksum_handler(req):
    event = req.split(",")
    s3_client.download_file(AWS_S3_Full, "original/" + event[0], "/tmp/temp")
    with open("/tmp/temp", "rb") as check:
        data = check.read()
        md5 = hashlib.md5(data).hexdigest()
    if event[1] == md5:
        s3_client.upload_file("/tmp/temp", AWS_S3_Full, "checksumed/"+event[0])
        return "success"
    return "failed"

def zip_handler(req):
    event = req.split(",")
    s3_client.download_file(AWS_S3_Full, "checksumed/" + event[0] , "/tmp/temp")
    with ZipFile('/tmp/temp.zip', 'w') as zip:
        zip.write("/tmp/temp")
    s3_client.upload_file("/tmp/temp.zip", AWS_S3_Full, "ziped/"+event[0]+".zip")
    return "success"

def encrypt_handler(req):
    event = req.split(",")
    s3_client.download_file(AWS_S3_Full, "ziped/" + event[0] + ".zip", "/tmp/temp.zip")
    key = Fernet.generate_key()
    with open('/tmp/temp.key', 'wb') as filekey:
        filekey.write(key)
    fernet = Fernet(key)
    data = ""
    with open("/tmp/temp.zip", "rb") as file:
        data = file.read()
    encrypted_data = fernet.encrypt(data)
    with open("/tmp/temp.zip", "wb") as file:
        file.write(encrypted_data)
    s3_client.upload_file("/tmp/temp.zip", AWS_S3_Full, "encrypted/"+event[0]+".zip")
    s3_client.upload_file("/tmp/temp.key", AWS_S3_Full, "encrypted/"+event[0]+".key")
    return "success"

def handle_handler(req):
    event = json.loads(req, strict=False)
    idx = event["manifest"].find("\n")
    to_checksum = event["manifest"][:idx]
    to_zip = event["to_zip"]
    to_encrypt = event["to_encrypt"]
    new_manifest = event["manifest"][idx+1:]

    fs = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        if to_checksum != "":
            fs.append(executor.submit(checksum_handler, to_checksum))
        if to_zip != "":
            fs.append(executor.submit(zip_handler, to_zip))
        if to_encrypt != "":
            fs.append(executor.submit(encrypt_handler, to_encrypt))
    results = [f.result() for f in fs]
    if to_checksum != "" or to_zip != "":
        if to_checksum != "" and "success" not in results[0]:
            to_checksum = ""
        return handle_handler(json.dumps({"manifest": new_manifest, "to_zip": to_checksum, "to_encrypt": to_zip}))
    return "success"

def handle(req):
    event = json.loads(req, strict=False)
    idx = event["manifest"].find("\n")
    to_checksum = event["manifest"][:idx]
    to_zip = event["to_zip"]
    to_encrypt = event["to_encrypt"]
    new_manifest = event["manifest"][idx+1:]

    fs = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        if to_checksum != "":
            fs.append(executor.submit(checksum_handler, to_checksum))
        if to_zip != "":
            fs.append(executor.submit(zip_handler, to_zip))
        if to_encrypt != "":
            fs.append(executor.submit(encrypt_handler, to_encrypt))
    results = [f.result() for f in fs]
    if to_checksum != "" or to_zip != "":
        if to_checksum != "" and "success" not in results[0]:
            to_checksum = ""
        return handle_handler(json.dumps({"manifest": new_manifest, "to_zip": to_checksum, "to_encrypt": to_zip}))
    return "success"
