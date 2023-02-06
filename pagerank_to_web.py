import pandas as pd
import numpy as np
import json
import operator
from hdfs import InsecureClient

client = InsecureClient('http://master-node:9870', user='hdfs')

with client.read("/user/hadoop/output_ranks.csv", encoding='utf-8') as reader:
    pagerank_result = pd.read_csv(reader, names=['float_id', 'w'])

pagerank_result['id'] = pagerank_result['float_id'].apply(int)
pagerank_result['rank'] = pagerank_result['w'].rank(
    method='min', ascending=False).apply(int)
