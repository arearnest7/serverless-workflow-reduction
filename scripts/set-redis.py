import json
import pprint
import csv
import os
import sys
import redis

def main():
    redisPassword = sys.argv[1]
    redisHostname = "127.0.0.1"
    redisPort = 6379
    redisClient = redis.Redis(
                    host=redisHostname,
                    port=redisPort,
                    password=redisPassword,
                )

    video = ["min_0.mp4", "min_0909.mp4", "min_1.mp4", "min_2.mp4", "min_3.mp4", "min_4.mp4", "min_5.mp4"]
    for i in range(10000):
        with open("raw/" + str(i), "r") as f:
            data = f.read()
            redisClient.set("raw-" + str(i), data)
    with open("review.csv", "r") as f:
        data = f.read()
        redisClient.set("review.csv", data)
    for v in video:
        with open("Video_Src/" + v, "rb") as f:
            data = f.read()
            redisClient.set("Video_Src/" + v, data)
            redisClient.set("original-" + v, data)
main()
