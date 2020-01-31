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
import os
import shlex, subprocess
import json
import infer_tap
import tap as tap

bucket = 'preprocess'

client = Minio('localhost:9000',
               access_key='admin',
               secret_key='password',
               secure=False)

# Put a file with default content-type.
events = client.listen_bucket_notification(bucket, '',
                                           '',
                                           ['s3:ObjectCreated:*'])

user = 'raymond'
tempFolder = '/home/'+user+'/Tap/dataset/tap/temp/'

for event in events:
	#print (event)
	fileName = event["Records"][0]["s3"]["object"]["key"]
	fileNameWOExt = os.path.splitext(fileName)[0]
	print (fileNameWOExt)
	print(client.fget_object(bucket, fileName, tempFolder+fileName))
	
	tap.create_manifest(data_dir='./dataset/tap/temp', manifest_path='manifest.TAP')
	infer_tap.infer(fileNameWOExt)