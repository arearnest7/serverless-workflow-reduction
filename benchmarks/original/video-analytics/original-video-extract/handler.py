#!/usr/bin/env python
import os
from urllib.parse import unquote_plus
import json
import subprocess
import re
import time
import redis

FFMPEG_STATIC = "function/var/ffmpeg"

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
    event = json.loads(req)
    if('dummy' in event) and (event['dummy'] == 1):
        print("Dummy call, doing nothing")
        return {"Extract Got Dummy" : "Dummy call, doing nothing"}

    #print(subprocess.call([FFMPEG_STATIC]))
    #s3_client = boto3.client(
    #    's3',
    #    aws_access_key_id=AWS_AccessKey,
    #    aws_secret_access_key=AWS_SecretAccessKey
    #)
    #config = TransferConfig(use_threads=False)
    #bucket_name = AWS_S3_Original
    print(event)
    list_of_chunks = event['values']
    src_video = event['source_id']
    millis_list = event['millis']
    detect_prob = event['detect_prob']
    count=0
    extract_millis = []
    for record in list_of_chunks:
        filename = "/tmp/chunk_" + str(record) + ".mp4"
        f = open(filename, "wb")
        key = "Video_Chunks_Step/min_"+str(src_video)
        key = key +"_"+str(record)+"_"
        key = key + str(millis_list[count])+".mp4"

        count = count + 1

        #s3_client.download_fileobj(bucket_name, key , f, Config=config)
        data = redisClient.get(key)
        f.write(data)
        f.close()
        millis = int(round(time.time() * 1000))
        extract_millis.append(millis)

        frame_name = key.replace("Video_Chunks_Step/","").replace("min", "frame").replace(".mp4","_" + str(millis) + ".jpg")
        subprocess.call([FFMPEG_STATIC, '-i', filename, '-frames:v', "1" , "-q:v","1", '/tmp/'+frame_name])
        try:
            #s3_client.upload_file("/tmp/"+frame_name, bucket_name, "Video_Frames_Step/"+frame_name, Config=config)
            with open("/tmp/"+frame_name, "rb") as f:
                data = f.read()
                redisClient.set("Video_Frames_Step/"+frame_name, data)
        except:
            #s3_client.upload_file("function/var/Frame_1.jpg", bucket_name, "Video_Frames_Step/"+frame_name, Config=config)
            with open("function/var/Frame_1.jpg", "rb") as f:
                data = f.read()
                redisClient.set("Video_Frames_Step/"+frame_name, data)
    print("Done!") 

    obj= {
        'statusCode': 200,
        'counter': count,
        'millis1': millis_list,
        'millis2': extract_millis,
        'source_id': src_video,
        'detect_prob': detect_prob,     
        'values': list_of_chunks,
        'body': json.dumps('Download/Split/Upload Successful!'),
        
    }
    #print(obj)
    return json.dumps(obj)
