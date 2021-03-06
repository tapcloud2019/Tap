from deeppavlov import configs, build_model
import logging
import json
from minio import Minio
from minio import CopyConditions
from minio.error import ResponseError
import glob, os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys

user = 'raymond'

class Watcher:
    DIRECTORY_TO_WATCH = "/home/"+user+"/Tap/dataset/tap/transcription"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print("Received created event - %s." % event.src_path)
            Handler.ner_upload()

        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            print("Received modified event - %s." % event.src_path)

    @staticmethod
    def ner_upload():
        os.chdir('/home/'+user+'/Tap/dataset/tap/transcription')
        transript_file = ''
        for file in glob.glob("*.txt"):
            transript_file = file

        transript_fileWOExt = os.path.splitext(transript_file)[0]

        with open(transript_file, 'r') as file:
            transript = file.read().replace('\n', '')
        print(transript)

        # logging.getLogger("deeppavlov").propagate = False
        try:
            ner_model = build_model(configs.ner.ner_ontonotes_bert, download=False)
        except:
            print("An exception occurred")
            
        ner = ner_model([transript])

        fileNameWOExt = os.path.splitext(transript_file)[0]

        ACCESS_KEY = "admin"
        SECRET_KEY = "password"

        #Initialise MinioClient
        minioClient = Minio('127.0.0.1:9000', access_key= ACCESS_KEY, secret_key= SECRET_KEY, secure=False)

        # Insert output from Deepspeech into this variable
        metadata = {"Transcript": transript, "Entities": json.dumps(ner)}
        print(metadata)
        print('metadata size: ' + str(sys.getsizeof(metadata)))

        # Append metadata onto original video and upload to new Minio Bucket
        found = False
        try:
            print('before minio stat object')
            print(minioClient.stat_object("video", transript_fileWOExt+".mp4"))
            found = True
            print('after minio stat object')
        except:
            print('Error in found')
        if (found):
            print('found')
            try:
                copy_result = minioClient.copy_object("postprocess", transript_fileWOExt+".mp4", "video/"+transript_fileWOExt+".mp4", metadata=metadata)
                os.remove('/home/'+user+'/Tap/dataset/tap/transcription/'+transript_file)
            except:
                print('error')
                os.remove('/home/'+user+'/Tap/dataset/tap/transcription/'+transript_file)
        else:
            print('not found')
            try:
                copy_result = minioClient.copy_object("postprocess", transript_fileWOExt+".WAV", "preprocess/"+transript_fileWOExt+".WAV", metadata=metadata)
                os.remove('/home/'+user+'/Tap/dataset/tap/transcription/'+transript_file)
            except:
                print('error')
                os.remove('/home/'+user+'/Tap/dataset/tap/transcription/'+transript_file)

if __name__ == '__main__':
    w = Watcher()
    w.run()


