import requests
import json
import os
import sys
import redis

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

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
    params = json.loads(req)
    #s3.download_file(AWS_S3_Original, params["operator"], "/tmp/temp")
    temp = json.loads(redisClient.get(params["operator"]))
    params["operator"] = temp["operator"]
    params["id"] = temp["id"]
    stats = {'total': params['total']['statistics']['total'] }
    params['statistics'] = stats

    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-wage-avg', data = json.dumps(params))
    return response.text
