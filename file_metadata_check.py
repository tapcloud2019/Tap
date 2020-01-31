from minio import Minio
from minio.error import ResponseError
import os
import subprocess
import json

user = 'raymond'
tempFolder = '/home/'+user+'/Tap/dataset/tap/temp/'

fileToCheck = '000011742.WAV'

ACCESS_KEY = "admin"
SECRET_KEY = "password"

#Initialise MinioClient
minioClient = Minio('127.0.0.1:9000', access_key= ACCESS_KEY, secret_key= SECRET_KEY, secure=False)

# Error-Checking to validate metadata has been appended to the corresponding video
try:
    print(minioClient.fget_object("postprocess", fileToCheck, tempFolder + fileToCheck))
except ResponseError as err:
    print(err)