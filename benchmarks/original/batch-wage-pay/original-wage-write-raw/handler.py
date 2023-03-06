import requests
import json
import redis

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

def handle(req):
    params = json.loads(req)
    #with open("/tmp/temp", "w") as f:
    #    f.write(req)
    #f.close()
    #s3.upload_file("/tmp/temp", AWS_S3_Original, "raw/" + str(params["id"]))
    redisClient.set("raw-" + str(params["id"]), req)
    response = requests.get(url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-wage-stats', data = json.dumps(params))
    return response.text
