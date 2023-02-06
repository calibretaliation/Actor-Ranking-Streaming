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

with client.read("/user/hadoop/actors.csv", encoding='utf-8') as reader:
    actors = pd.read_csv(reader)

with client.read("/user/hadoop/popularity_weight.csv", encoding='utf-8') as reader:
    weight = pd.read_csv(reader)

weight.rename(columns={"actor1": "source", "actor2": "target"}, inplace=True)
weight = weight[weight['source'].isin(
    pagerank_result['id']) & weight['target'].isin(pagerank_result['id'])]

weight['source'] = weight['source'].apply(str)
weight['target'] = weight['target'].apply(str)

data = pd.merge(actors, pagerank_result, on="id", how="inner")

web_data = {'nodes': [], 'links': weight.to_dict('records')}

for i, r in data.iterrows():
    web_data['nodes'].append({
        'id': str(r['id']),
        'color': 'cyan' if r['gender'] == 2 else 'pink',
        'size': 5*range(10, 0, -1)[r['rank']-1] if r['rank'] <= 10 else 1,
        'popularity': int(r['popularity']),
        'label': r['name'],
        'rank': r['rank'],
    })

with open("data.json", "w") as outfile:
    json.dump(web_data, outfile, indent=4)
