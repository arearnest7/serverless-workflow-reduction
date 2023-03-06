import os
import json
import string
import hashlib
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
    data = redisClient.get("original-" + event[0])
    md5 = hashlib.md5(data).hexdigest()
    if event[1] == md5:
        redisClient.set("checksumed-" + event[0], data)
        return "success"
    return "failed"
