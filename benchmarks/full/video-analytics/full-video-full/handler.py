#!/usr/bin/env python
import os
import json
import boto3
from boto3.s3.transfer import TransferConfig
import subprocess
import re
import time
import requests
import random
from urllib.parse import unquote_plus
import sys
from imageai.Detection import ObjectDetection
from multiprocessing import Process, Manager
import multiprocessing
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageFile
import zipfile
from concurrent.futures import ThreadPoolExecutor

FFMPEG_STATIC = "function/var/ffmpeg"

length_regexp = 'Duration: (\d{2}):(\d{2}):(\d{2})\.\d+,'
re_length = re.compile(length_regexp)

ImageFile.LOAD_TRUNCATED_IMAGES = True

with open("/var/openfaas/secrets/aws-access-key", "r") as f:
    AWS_AccessKey=f.read()
with open("/var/openfaas/secrets/aws-secret-access-key", "r") as f:
    AWS_SecretAccessKey=f.read()
with open("/var/openfaas/secrets/aws-s3-full", "r") as f:
    AWS_S3_Full=f.read()

def delete_tmp():
    for root, dirs, files in os.walk("./tmp/", topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))

def detect_object(index, index2, image, src_video, milli_1, milli_2, detect_prob):
    detector = ObjectDetection()
    model_path = "function/models/yolo-tiny.h5"

    start_time = int(round(time.time() * 1000))

    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_AccessKey,
        aws_secret_access_key=AWS_SecretAccessKey
    )
    config = TransferConfig(use_threads=False)
    bucket_name = AWS_S3_Full

    worker_dir = "/tmp/" + "Worker_" + str(index)
    if not os.path.exists(worker_dir):
        os.mkdir(worker_dir)

    filename = worker_dir + "/image_" + str(index) + ".jpg"
    f = open(filename, "wb")
    key = image
    s3_client.download_fileobj(bucket_name, key , f, Config=config)
    f.close()
    print("Download duration: " + str(time.time() * 1000 - start_time))
    #input_path = "~/images/input_fast.jpg"
    #if(index == 29):
    #   input_path = "~/images/input_slow.jpg"

    output_path = "function/images/output_" + str(index) + ".jpg"
    detector.setModelTypeAsTinyYOLOv3()

    detector.setModelPath(model_path)
    detector.loadModel()

    start_time = time.time() * 1000

    detection = detector.detectObjectsFromImage(input_image=filename, output_image_path=output_path,  minimum_percentage_probability=detect_prob)

    for box in range(len(detection)):
        print(detection[box])

    if (len(detection)>10):
        original_image = Image.open(filename, mode='r')
        ths = []
        threads=10
        start_index = 0
        step_size = int(len(detection) / threads) + 1

        for t in range(threads):
            end_index = min(start_index + step_size , len(detection))
            ths.append(Process(target=crop_and_sharpen, args=(original_image.copy(), t, detection, start_index , end_index, worker_dir)))
            start_index = end_index
        for t in range(threads):
            ths[t].start()
        for t in range(threads):
            ths[t].join()
    millis_3 = int(round(time.time() * 1000))
    zipFileName = "detected_images_" + str(src_video)+ "_" + str(index) + "_" + str(milli_1[0]) + "_" + str(milli_2[0]) + "_"  + str(millis_3) +  ".zip"
    myzip = zipfile.ZipFile("/tmp/" + zipFileName, 'w', zipfile.ZIP_DEFLATED)

    for f in os.listdir(worker_dir):
        myzip.write(worker_dir + "/" + f)

    s3_client.upload_file("/tmp/" + zipFileName, bucket_name, "Detected_Objects/" + zipFileName, Config=config)
    print("file uploaded " + zipFileName)

def crop_and_sharpen(original_image, t, detection ,start_index, end_index, worker_dir):
    for box in range(start_index, end_index):
            im_temp = original_image.crop((detection[box]['box_points'][0], detection[box]['box_points'][1], detection[box]['box_points'][2], detection[box]['box_points'][3]))
            im_resized = im_temp.resize((1408, 1408))
            im_resized_sharpened =  im_resized.filter(ImageFilter.SHARPEN)
            fileName = worker_dir + "/" + detection[box]['name']  + "_" + str(box) + "_" + str(t) + "_" + ".jpg"
            im_resized_sharpened.save(fileName)
            #im_temp.save(fileName)

    #print(detection) 
    print(len(detection))

def classify_handler(req):
    event = json.loads(req)
    if('dummy' in event) and (event['dummy'] == 1):
        print("Dummy call, doing nothing")
        return
    start_time = int(round(time.time() * 1000))

    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_AccessKey,
        aws_secret_access_key=AWS_SecretAccessKey
    )
    #config = TransferConfig(use_threads=False)
    print(event)
    bucket_name = AWS_S3_Full

    list_of_chunks = event['values']
    #list_of_images = event['images']

    print(list_of_chunks[0])
    src_video = event['source_id']
    millis_list1 = event['millis1']
    millis_list2 = event['millis2']
    detect_prob = event['detect_prob']

    ths=[]
    num_workers = len(list_of_chunks)
    for w in range(num_workers):

        key="Video_Frames_Step/frame_" + str(src_video) + "_" + str(list_of_chunks[w]) + "_" + str(millis_list1[w]) + "_" + str(millis_list2[w]) + ".jpg"
        ths.append(Process(target=detect_object,  args=(list_of_chunks[w], list_of_chunks[w], key, src_video, millis_list1, millis_list2, detect_prob)))

    for t in range(num_workers):
        ths[t].start()
    for t in range(num_workers):
        ths[t].join()

    end_time = time.time() * 1000
    diff_time = str( end_time  - start_time )
    print("duration: " + str(end_time-start_time))
    return json.dumps({ 'duration': diff_time, 'values': str(event['values']) })
    delete_tmp()

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
    bucket_name = AWS_S3_Full
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
            s3_client.upload_file("function/var/Frame_1.jpg", bucket_name, "Video_Frames_Step/"+frame_name, Config=config)
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
        counter_out=event[str(eve)]["counter"]
        src_id_out=event[str(eve)]["source_id"]
        detect_prob=event[str(eve)]["detect_prob"]
        for c in range(event[str(eve)]["counter"]):
            val = event[str(eve)]["values"][c]
            m1 = event[str(eve)]["millis1"][c]
            m2 = event[str(eve)]["millis2"][c]
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
            fs.append(executor.submit(classify_handler, json.dumps(returnedDic["detail"]["indeces"][i])))
    results = [f.result() for f in fs]
    return json.dumps(results)

def handle(req):
    event = json.loads(req)
    if('dummy' in event) and (event['dummy'] == 1):
        print(AWS_AccessKey)
        print(AWS_SecretAccessKey)
        print(AWS_S3_Full)
        print("Dummy call, doing nothing")
        return

    #print(subprocess.call([FFMPEG_STATIC]))
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_AccessKey,
        aws_secret_access_key=AWS_SecretAccessKey
    )
    bucket_name = AWS_S3_Full
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
            fs.append(executor.submit(extract_handler, json.dumps(listOfDics[i])))
    results = [json.loads(f.result()) for f in fs]
    payload = {}
    for i in range(len(results)):
        payload[str(i)] = results[i]
    print(payload)
    results = shuffle_handler(json.dumps(payload))
    return results
