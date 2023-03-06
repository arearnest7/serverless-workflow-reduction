import json
import redis

def handle(req):
    params = json.loads(req)

    #with open("/tmp/temp", "w") as f:
    #    f.write(req)
    #f.close()
    #s3.upload_file("/tmp/temp", AWS_S3_Original, "merit/" + str(params["id"]))
    redisClient.set("merit-" + str(params["id"]), req)

    return str(params["id"]) + " statistics uploaded/updated"
