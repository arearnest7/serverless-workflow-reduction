import requests
import os
import json
import string
from concurrent.futures import ThreadPoolExecutor
import hashlib
from zipfile import ZipFile
from cryptography.fernet import Fernet
import redis

with open('/var/openfaas/secrets/redis-password', 'r') as s:
    redisPassword = s.read()
redisHostname = os.getenv('redis_hostname')
redisPort = os.getenv('redis_port')
redisClient = redis.Redis(
                host=redisHostname,
                port=redisPort,
                password=redisPassword,
            )

def checksum_handler(req):
    event = req.split(",")
    data = redisClient.get("original-" + event[0])
    md5 = hashlib.md5(data).hexdigest()
    if event[1] == md5:
        redisClient.set("checksumed-" + event[0], data)
        return "success"
    return "failed"

def zip_handler(req):
    event = req.split(",")
    data = redisClient.get("checksumed-" + event[0])
    with open("/tmp/" + event[0], "w") as f:
        f.write(data)
    with ZipFile('/tmp/zip.zip', 'w') as zip:
        zip.write("/tmp/" + event[0])
    zip.close()
    with open("/tmp/zip.zip", "w") as f:
        data = f.read()
    redisClient.set("ziped-" + event[0], data)
    return "success"

def encrypt_handler(req):
    event = req.split(",")
    data = redisClient.get("ziped-" + event[0])
    with open("/tmp/" + event[0] + ".zip", "w") as f:
        f.write(data)
    key = Fernet.generate_key()
    with open('/tmp/key.key', 'wb') as filekey:
        filekey.write(key)
    filekey.close()
    fernet = Fernet(key)
    data = ""
    with open("/tmp/" + event[0] + ".zip", "rb") as file:
        data = file.read()
    file.close()
    encrypted_data = fernet.encrypt(data)
    redisClient.set("encrypted-" + event[0], encrypted_data)
    redisClient.set("encrypted-key-" + event[0], key)
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
