from zipfile import ZipFile
import os
import json
import string
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

def handle(req):
    event = req.split(",")
    data = redisClient.get("checksumed-" + event[0])
    with open("/tmp/" + event[0], "wb") as f:
        f.write(data)
    with ZipFile('/tmp/zip.zip', 'w') as zip:
        zip.write("/tmp/" + event[0])
    zip.close()
    with open("/tmp/zip.zip", "rb") as f:
        data = f.read()
    redisClient.set("ziped-" + event[0], data)
    return "success"
