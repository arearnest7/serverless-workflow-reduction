import os
import json
import string
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

def handle(req):
    event = req.split(",")
    data = redisClient.get("ziped-" + event[0])
    with open("/tmp/" + event[0] + ".zip", "wb") as f:
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
