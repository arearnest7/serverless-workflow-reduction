import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor
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
    manifest = s3.list_objects(Bucket=AWS_S3_Original, Prefix="raw/")

    total = {'statistics': {'total': 0, 'staff-number': 0, 'teamleader-number': 0, 'manager-number': 0}}
    base = {'statistics': {'staff': 0, 'teamleader': 0, 'manager': 0}}
    merit = {'statistics': {'staff': 0, 'teamleader': 0, 'manager': 0}}

    for obj in redisClient.scan_iter("raw-*"):
        #s3.download_file(AWS_S3_Original, obj["Key"], "/tmp/temp")
        #doc = {}
        #with open("/tmp/temp", "r") as f:
        #    doc = json.load(f)
        doc = json.loads(redisClient.get(key))
        total['statistics']['total'] += doc['total']
        total['statistics'][doc['role']+'-number'] += 1
        base['statistics'][doc['role']] += doc['base']
        merit['statistics'][doc['role']] += doc['merit']

    fs = []
    with ThreadPoolExecutor(max_workers=len(manifest["Contents"])) as executor:
        for obj in manifest["Contents"]:
            if obj["Key"] != "raw/":
                fs.append(executor.submit(requests.get, url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-wage-sum', data = json.dumps({'total': total, 'base': base, 'merit': merit, 'operator': obj["Key"]})))
    results = [f for f in fs]
    return "processed batch at " + str(time.time())
