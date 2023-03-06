import requests
import json
import random
from concurrent.futures import ThreadPoolExecutor
import redis

OF_Gateway_IP="gateway.openfaas"
OF_Gateway_Port="8080"

def handle(req):
    event = json.loads(req)
    # TODO implement
    # Remove below line for ORG DAG
    #event = event["detail"]["indeces"]
    #print(event)
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
    
    #print(trips)
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
            fs.append(executor.submit(requests.get, url = 'http://' + OF_Gateway_IP + ':' + OF_Gateway_Port + '/function/original-video-classify', data = json.dumps(returnedDic["detail"]["indeces"][i])))
    results = [f.result().text for f in fs]
    print(results)
    return json.dumps(results)
