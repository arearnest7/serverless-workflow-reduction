import requests
import os
import json
import string
from concurrent.futures import ThreadPoolExecutor

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

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
            fs.append(executor.submit(requests.get, url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/partial-batch-partial-checksum' , data = to_checksum))
        if to_zip != "":
            fs.append(executor.submit(requests.get, url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/partial-batch-partial-zip' , data = to_zip))
        if to_encrypt != "":
            fs.append(executor.submit(requests.get, url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/partial-batch=partial-encrypt' , data = to_encrypt))
    results = [f.result().text for f in fs]
    if to_checksum != "" or to_zip != "":
        if to_checksum != "" and "success" not in results[0]:
            to_checksum = ""
        return handle_handler({"manifest": new_manifest, "to_zip": to_checksum, "to_encrypt": to_zip})
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
            fs.append(executor.submit(requests.get, url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/partial-batch-partial-checksum' , data = to_checksum))
        if to_zip != "":
            fs.append(executor.submit(requests.get, url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/partial-batch-partial-zip' , data = to_zip))
        if to_encrypt != "":
            fs.append(executor.submit(requests.get, url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/partial-batch=partial-encrypt' , data = to_encrypt))
    results = [f.result().text for f in fs]
    if to_checksum != "" or to_zip != "":
        if to_checksum != "" and "success" not in results[0]:
            to_checksum = ""
        return handle_handler({"manifest": new_manifest, "to_zip": to_checksum, "to_encrypt": to_zip})
    return "success"
