import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor
import redis

TAX = 0.0387
INSURANCE = 1500
ROLES = ['staff', 'teamleader', 'manager']
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

def write_merit_handler(req):
    params = json.loads(req)

    #with open("/tmp/temp", "w") as f:
    #    f.write(req)
    #f.close()
    #s3.upload_file("/tmp/temp", AWS_S3_Full, "merit/" + str(params["id"]))
    redisClient.set("merit-" + str(params["id"]), req)

    return str(params["id"]) + " statistics uploaded/updated"

def wage_merit_handler(req):
    params = json.loads(req)
    meritp = {'staff': 0, 'teamleader': 0, 'manager': 0}
    for role in ROLES:
        num = params['total']['statistics'][role+'-number']
        if num != 0:
            base = params['base']['statistics'][role]
        merit = params['merit']['statistics'][role]
        meritp[role] = merit / base
    params['statistics']['average-merit-percent'] = meritp
    return write_merit_handler(json.dumps({'id': params['id'], 'statistics': params['statistics'], 'operator' : params['operator']}))

def wage_avg_handler(req):
    params = json.loads(req)

    realpay = {'staff': 0, 'teamleader': 0, 'manager': 0}
    for role in ROLES:
        num = params['total']['statistics'][role+'-number']
        if num != 0:
            base = params['base']['statistics'][role]
            merit = params['merit']['statistics'][role]
            realpay[role] = (1-TAX) * (base + merit) / num
    params['statistics']['average-realpay'] = realpay

    return wage_merit_handler(json.dumps(params))

def wage_sum_handler(req):
    params = json.loads(req)
    #s3.download_file(AWS_S3_Full, params["operator"], "/tmp/temp")
    temp = json.loads(redisClient.get(params["operator"]))
    params["operator"] = temp["operator"]
    params["id"] = temp["id"]
    stats = {'total': params['total']['statistics']['total'] }
    params['statistics'] = stats

    return wage_avg_handler(json.dumps(params))

def stats_handler(req):
    #manifest = s3.list_objects(Bucket=AWS_S3_Full, Prefix="raw/")

    total = {'statistics': {'total': 0, 'staff-number': 0, 'teamleader-number': 0, 'manager-number': 0}}
    base = {'statistics': {'staff': 0, 'teamleader': 0, 'manager': 0}}
    merit = {'statistics': {'staff': 0, 'teamleader': 0, 'manager': 0}}

    for key in redisClient.scan_iter("raw-*"):
        #s3.download_file(AWS_S3_Full, obj["Key"], "/tmp/temp")
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
                fs.append(executor.submit(wage_sum_handler, json.dumps({'total': total, 'base': base, 'merit': merit, 'operator': obj["Key"]})))
    results = [f for f in fs]
    return "processed batch at " + str(time.time())

def write_raw_handler(req):
    params = json.loads(req)
    #with open("/tmp/temp", "w") as f:
    #    f.write(req)
    #f.close()
    #s3.upload_file("/tmp/temp", AWS_S3_Full, "raw/" + str(params["id"]))
    redisClient.set("raw-" + str(params["id"]), req)
    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/full-wage-full', data = json.dumps(req))
    return response.text

def format_handler(req):
    params = json.loads(req)
    params['INSURANCE'] = INSURANCE

    total = INSURANCE + params['base'] + params['merit']
    params['total'] = total

    realpay = (1-TAX) * (params['base'] + params['merit'])
    params['realpay'] = realpay

    return write_raw_handler(json.dumps(params))

def validator_handler(req):
    event = json.loads(req)
    for param in ['id', 'name', 'role', 'base', 'merit', 'operator']:
        if param in ['name', 'role']:
            if not isinstance(event[param], str):
                return "fail: illegal params: " + str(event[param]) + " not string"
            elif param == 'role' and event[param] not in ROLES:
                return "fail: invalid role: " + str(event[param])
        elif param in ['id', 'operator']:
            if not isinstance(event[param], int):
                return "fail: illegal params: " + str(event[param]) + " not integer"
        elif param in ['base', 'merit']:
            if not isinstance(event[param], float):
                return "fail: illegal params: " + str(event[param]) + " not float"
            elif event[param] < 1 or event[param] > 8:
                return "fail: illegal params: " + str(event[param]) + " not between 1 and 8 inclusively"
        else:
            return "fail: missing param: " + param
    return format_handler(req)

def handle(req):
    params = json.loads(req)
    response = ""
    if isinstance(params, dict):
        response = validator_handler(req)
    else:
        response = stats_handler(req)
    return response
