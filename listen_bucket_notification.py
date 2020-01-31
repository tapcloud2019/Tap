# -*- coding: utf-8 -*-
# MinIO Python Library for Amazon S3 Compatible Cloud Storage.
# Copyright (C) 2016 MinIO, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Note: YOUR-ACCESSKEYID, YOUR-SECRETACCESSKEY, my-testfile, my-bucketname and
# my-objectname are dummy values, please replace them with original values.

from minio import Minio
from minio.error import ResponseError
import os
import subprocess
import json

bucket = 'video'

client = Minio('localhost:9000',
               access_key='admin',
               secret_key='password',
               secure=False)

# Put a file with default content-type.
events = client.listen_bucket_notification(bucket, '',
                                           '',
                                           ['s3:ObjectCreated:*'])

user = 'raymond'
vidsFolder = '/home/'+user+'/Tap/dataset/tap/videos/'
tempFolder = '/home/'+user+'/Tap/dataset/tap/temp/'

for event in events:
	# print(event)
	fileName = event["Records"][0]["s3"]["object"]["key"]
	fileNameWOExt = os.path.splitext(fileName)[0]
	print(fileNameWOExt)
	try:
		print(client.fget_object(bucket, fileName, vidsFolder+fileName))
	except ResponseError as err:
		print(err)
	myCmd = 'ffmpeg -i '+vidsFolder+fileName+' -ab 64k -ac 2 -ar 16000 -vn '+tempFolder+fileNameWOExt+'.WAV'
	os.system(myCmd)
	tempFile = tempFolder+fileNameWOExt+'.WAV'
	tempFileName = fileNameWOExt+'.WAV'
	print(tempFile)
	try:
		with open(tempFile, 'rb') as file_data:
			file_stat = os.stat(tempFile)
			print(file_stat.st_size)
			client.put_object('preprocess', tempFileName, file_data, file_stat.st_size, content_type='audio/wav')
		os.remove(vidsFolder+fileName)
		os.remove(tempFile)
	except ResponseError as err:
		print(err)
