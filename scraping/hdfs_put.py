import subprocess
import config
import time 
import sys
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

def hdfs_put(local_file_path, hdfs_file_path):
    command = config.HDFS_PUT_COMMAND
    if local_file_path is not None:
        command[-2] = local_file_path
    if hdfs_file_path is not None:    
        command[-1] = hdfs_file_path
    subprocess.Popen(["echo", str(command)])
    return command

def hdfs_delete(hdfs_file_path):
    command = config.HDFS_RM_COMMAND
    if hdfs_file_path is not None:    
        command[-1] = hdfs_file_path
    subprocess.Popen(["echo", str(command)])
    return command

class Event(PatternMatchingEventHandler):
    def on_created(self, event):
        hdfs_put(local_file_path = event.src_path, hdfs_file_path = config.HDFS_FOLDER)
        print(f"{event.src_path} created")
    def on_modified(self, event):
        hdfs_put(local_file_path = event.src_path, hdfs_file_path = config.HDFS_FOLDER)
        print(f"{event.src_path} modified")
    def on_moved(self, event):
        hdfs_put(local_file_path = event.src_path, hdfs_file_path = config.HDFS_FOLDER)
        print(f"{event.src_path} moved")
    def on_deleted(self, event):
        hdfs_file_path = config.HDFS_FOLDER + event.src_path
        hdfs_delete(hdfs_file_path = hdfs_file_path)
        print(f"{event.src_path} deleted")       
        
def watch_folder(observer, path = "/home/hadoop/"):
    event_handler = Event(patterns=["*.json"])
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
def stop_watch_folder(observer):
    observer.stop()
    observer.join()