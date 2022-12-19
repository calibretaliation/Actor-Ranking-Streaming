In this module:
1. Scraping
2. Put any scaped file to hadoop cluster
+ Requirements: requirments.txt and hadoop cluster already on
+ Run: 
from hdfs_put import watch_folder, stop_watch_folder
from watchdog.observers import Observer
observer = Observer()
watch_folder(observer, path/to/scraping/destination)
#when done running
stop_watch_folder(observer)