# TAP

## MinIO: http://localhost:9000/minio/video/  

### 1) Converts Video to Audio file (Video to preprocess bucket):  
**Description:** listen_bucket_notification.py listens for any file upload to video bucket. It will then convert the video file to audio and upload it to preprocess bucket.

**Python Environment:** Python 3

**Command for activating required Python Virtual Environment:**  
Open a new terminal
> source ~/PythonEnv/py3_deeppavlov/bin/activate  

**Command for triggering the listener:**  
In the same terminal
> cd ~/Tap  
> python listen_bucket_notification.py  

### 2) Generate transcript from audio file (Preprocess bucket to local file system):  
**Description:** listen_preprocess_notif.py listens for any file upload to preprocess bucket. It will then take the audio file and pass it through the DeepSpeech2 engine to generate the transcript. The transcript would be temporarily saved to the local file system.

**Python Environment:** Python 2

**Command for activating required Python Virtual Environment:**  
Open a new terminal
> source ~/PythonEnv/DeepSpeech/bin/activate  

**Command for triggering the listener:**  
In the same terminal
> cd ~/Tap  
> python listen_preprocess_notif.py  

### 3) Generate NER tags for transcript and upload media file with new meta-data (Local file system to postprocess bucket):  
**Description:** ner_and_upload.py listens for any transcript file placed in the local file system. It will take the transcript and generate NER tags for it. It will then search for its original media file in minio and append the meta-data to the original media file. The media file will then be uploaded to the postprocess bucket.

**Python Environment:** Python 3

**Command for activating required Python Virtual Environment:**  
Open a new terminal
> source ~/PythonEnv/py3_deeppavlov/bin/activate  

**Command for triggering the listener:**  
In the same terminal
> cd ~/Tap  
> python ner_and_upload.py  

### 4) Rich Media Platform:  
**Description:** Front end for interfacing with MinIO. 
- Display rich media files with their meta-data.
- Able to play the recordings directly in browser.
- Display transcript of media file with colour coded named entity recognition tags, if any.

**Command to execute:**  
Open a new terminal
> cd ~/TAP_RMP_FE_2019  
> node /home/raymond/.yarn/bin/serve -s build  

## Rich Media Platform: http://localhost:5000/rmp  