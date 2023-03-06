import requests
import json
import redis

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

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
