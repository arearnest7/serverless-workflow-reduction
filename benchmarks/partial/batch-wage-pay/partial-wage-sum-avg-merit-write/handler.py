import requests
import json
import redis

TAX = 0.0387
ROLES = ['staff', 'teamleader', 'manager']
OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

def write_merit_handler(req):
    params = json.loads(req)

    #with open("/tmp/temp", "w") as f:
    #    f.write(req)
    #f.close()
    #s3.upload_file("/tmp/temp", AWS_S3_Partial, "merit/" + str(params["id"]))
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

def handle(req):
    params = json.loads(req)
    #s3.download_file(AWS_S3_Partial, params["operator"], "/tmp/temp")
    temp = json.loads(redisClient.get(params["operator"]))
    params["operator"] = temp["operator"]
    params["id"] = temp["id"]
    stats = {'total': params['total']['statistics']['total'] }
    params['statistics'] = stats

    return wage_avg_handler(json.dumps(params))
