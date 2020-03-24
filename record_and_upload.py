import logging
import json
from minio import Minio
from minio import CopyConditions
from minio.error import ResponseError
import glob, os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

user = 'raymond'

class Watcher:
    DIRECTORY_TO_WATCH = "/home/"+user+"/Tap/dataset/tap/recording"

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
        os.chdir('/home/'+user+'/Tap/dataset/tap/recording')
        
        tempFile = ''
        
        for file in glob.glob("*.WAV"):
            tempFile = file
        #     pre, ext = os.path.splitext(tempFile)
        #     os.rename(tempFile, pre + ".WAV")

        # for file in glob.glob("*.WAV"):
        #     tempFile = file

        fileNameWOExt = os.path.splitext(tempFile)[0]
        tempFileName = fileNameWOExt+'.WAV'

        bucket = 'preprocess'

        client = Minio('localhost:9000', access_key='admin', secret_key='password', secure=False)

        try:
            with open(tempFile, 'rb') as file_data:
                file_stat = os.stat(tempFile)
                print(file_stat.st_size)
                client.put_object('preprocess', tempFileName, file_data, file_stat.st_size, content_type='audio/wav')
            os.remove(tempFile)
        except ResponseError as err:
            print(err)

if __name__ == '__main__':
    w = Watcher()
    w.run()