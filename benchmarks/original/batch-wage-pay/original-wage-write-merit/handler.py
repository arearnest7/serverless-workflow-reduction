import boto3
import json

with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()
with open("/var/openfaas/secrets/aws-s3-original", "r") as f:
    AWS_S3_Original=f.read()

s3 = boto3.client('s3', aws_access_key_id=AWS_AccessKey, aws_secret_access_key=AWS_SecretAccessKey)

def handle(req):
    params = json.loads(req)

    with open("/tmp/temp", "w") as f:
        f.write(req)
    f.close()
    s3.upload_file("/tmp/temp", AWS_S3_Original, "merit/" + str(params["id"]))

    return str(params["id"]) + " statistics uploaded/updated"
