import socket
from threading import *
import time
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from pyarrow import fs
host = "192.168.2.20"
port = 4321
print(host,"://",port)

hdfs = fs.HadoopFileSystem(host, port, user="hdfs")

weight_temp = pd.read_csv("/home/calibretaliation/LinkedIn-Analysis/popularity_weight.csv")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind((host, port))
s.listen(1)
print('WAITING FOR CLIENT')

try:
    while True:
        conn, addr = s.accept()
        print('CONNECTED:', addr)
        try:
            for i, line in weight_temp.iterrows():
                data = f"{line[0]},{line[1]},{line[2]}" +"\n"
                conn.send(bytes(data, 'utf-8'))
                time.sleep(1)
                print(data)
            conn.close()
            print("CLOSED")
        except socket.error: pass
finally:
    s.close()
