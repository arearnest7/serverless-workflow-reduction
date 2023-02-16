#!/usr/bin/env python
import os
import json
import boto3
from boto3.s3.transfer import TransferConfig
import subprocess
import re
import time
import requests
from urllib.parse import unquote_plus

FFMPEG_STATIC = "function/var/ffmpeg"

length_regexp = 'Duration: (\d{2}):(\d{2}):(\d{2})\.\d+,'
re_length = re.compile(length_regexp)

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"
with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()
with open("/var/openfaas/secrets/aws-s3-partial", "r") as f:
    AWS_S3_Partial=f.read()

def shuffle_handler(req):
    event = json.loads(req)
    # TODO implement
    # Remove below line for ORG DAG
    #event = event["detail"]["indeces"]
    trips=[]
    counter_out=0
    src_id_out=""
    detect_prob=-1
    for eve in range(len(event)):
        counter_out=event[eve]["counter"]
        src_id_out=event[eve]["source_id"]
        detect_prob=event[eve]["detect_prob"]
        for c in range(event[eve]["counter"]):
            val = event[eve]["values"][c]
            m1 = event[eve]["millis1"][c]
            m2 = event[eve]["millis2"][c]
            trips.append((val,m1,m2))

    print(trips)
    #random.shuffle(trips)
    #print(trips)

    returnedDic={}
    #returnedDic["source_id"] = src_id_out
    returnedDic["detail"] = {}
    returnedDic["detail"]["indeces"] = []


    v=[]
    m1=[]
    m2=[]
    count=0
    step_size=len(event)
    for eve in range(len(event)):
        count=eve
        for t in range(counter_out):
            v.append(trips[count][0])
            m1.append(trips[count][1])
            m2.append(trips[count][2])
            count=count+step_size

        #print(v)
        #print(m1)
        #print(m2)

        obj= {
        'statusCode': 200,
        'counter': counter_out,
        'millis1': m1,
        'millis2': m2,
        'source_id': src_id_out,
        'detect_prob': detect_prob,
        'values': v,
        'body': json.dumps('Download/Split/Upload Successful!'),
        }
        returnedDic["detail"]["indeces"].append(obj)
        v=[]
        m1=[]
        m2=[]

    fs = []
    with ThreadPoolExecutor(max_workers=len(returnedDic["detail"]["indeces"])) as executor:
        for i in range(len(returnedDic["detail"]["indeces"])):
            fs.append(executor.submit(requests.get, url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/partial-video-classify', data = json.dumps(returnedDic["detail"]["indeces"][i])))
    results = [f.text for f in fs]
    return json.dumps(results)

def extract_handler(req):
    event = json.loads(req)
    if('dummy' in event) and (event['dummy'] == 1):
        print("Dummy call, doing nothing")
        return {"Extract Got Dummy" : "Dummy call, doing nothing"}

    #print(subprocess.call([FFMPEG_STATIC]))
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_AccessKey,
        aws_secret_access_key=AWS_SecretAccessKey
    )
    config = TransferConfig(use_threads=False)
    bucket_name = AWS_S3_Partial
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

        s3_client.download_fileobj(bucket_name, key , f, Config=config)
        f.close()
        millis = int(round(time.time() * 1000))
        extract_millis.append(millis)

        frame_name = key.replace("Video_Chunks_Step/","").replace("min", "frame").replace(".mp4","_" + str(millis) + ".jpg")
        subprocess.call([FFMPEG_STATIC, '-i', filename, '-frames:v', "1" , "-q:v","1", '/tmp/'+frame_name])
        try:
            s3_client.upload_file("/tmp/"+frame_name, bucket_name, "Video_Frames_Step/"+frame_name, Config=config)
        except:
            s3_client.upload_file("var/Frame_1.jpg", bucket_name, "Video_Frames_Step/"+frame_name, Config=config)
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
    return obj

def handle(req):
    event = json.loads(req)
    if('dummy' in event) and (event['dummy'] == 1):
         print(AWS_AccessKey)
         print(AWS_SecretAccessKey)
         print(bucketName) 
         print("Dummy call, doing nothing")
         return

    #print(subprocess.call([FFMPEG_STATIC]))
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_AccessKey,
        aws_secret_access_key=AWS_SecretAccessKey
    )
    bucket_name = AWS_S3_Partial
    config = TransferConfig(use_threads=False)
    filename = "/tmp/src.mp4"
    f = open(filename, "wb")
    print(event)
    src_video=event['src_name']
    DOP=int(event['DOP'])
    detect_prob=int(event['detect_prob'])
    s3_client.download_fileobj(bucket_name, "Video_Src/min_"+src_video+".mp4" , f, Config=config)
    f.close()

    output = subprocess.Popen(FFMPEG_STATIC + " -i '"+filename+"' 2>&1 | grep 'Duration'",
        shell = True,
        stdout = subprocess.PIPE
    ).stdout.read().decode("utf-8")

    print(output)
    matches = re_length.search(output)
    count=0
    millis_list=[]
    if matches:
        video_length = int(matches.group(1)) * 3600 + \
                    int(matches.group(2)) * 60 + \
                    int(matches.group(3))
        print("Video length in seconds: "+str(video_length))

        start=0
        chunk_size=2 # in seconds
        while (start < video_length):
            end=min(video_length-start,chunk_size)
            millis = int(round(time.time() * 1000))
            millis_list.append(millis)
            chunk_video_name = 'min_' + src_video + "_" + str(count) + "_" + str(millis) + '.mp4'
            subprocess.call([FFMPEG_STATIC, '-i', filename, '-ss', str(start) , '-t', str(end),'-c', 'copy', '/tmp/'+chunk_video_name])
              
            count=count+1
            start=start+chunk_size
            s3_client.upload_file("/tmp/" + chunk_video_name, bucket_name, "Video_Chunks_Step/"+chunk_video_name, Config=config)
    print("Done!") 

    payload=count/DOP
    listOfDics = []   
    currentList = []
    currentMillis = []
    for i in range(count):
        if len(currentList) < payload:
            currentList.append(i)
            currentMillis.append(millis_list[i]) 
        if len(currentList) == payload:
            tempDic = {}
            tempDic['values'] = currentList
            tempDic['source_id'] = src_video
            tempDic['millis'] = currentMillis
            tempDic['detect_prob'] = detect_prob        
            listOfDics.append(tempDic)
            currentList = []
            currentMillis = []

    returnedObj = {
      "detail": {
        "indeces": listOfDics 
        }
    }
    print(returnedObj)
    fs = []
    with ThreadPoolExecutor(max_workers=len(listOfDics)) as executor:
        for i in range(len(listOfDics)):
            fs.append(executor.submit(extract_handler, listOfDics[i]))
    results = [f for f in fs]
    payload = {}
    for i in range(len(results)):
        payload[i] = results[i]
    print(payload)
    results = shuffle_handler(json.dumps(payload))
    return results
