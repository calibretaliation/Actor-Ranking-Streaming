import urllib.request
import json
import itertools
import pandas as pd
from tqdm import tqdm
import numpy as np
from hdfs import InsecureClient
import os
from queue import Queue
from threading import Thread


key = '8c0c786aba77a3ff00ebb47ca9fa3b8f'
TEMP_WEIGHTS_DIR = '/user/hadoop/temp_weight'
WEIGHTS_DIR = '/user/hadoop/weight'
added_actors = []
client = InsecureClient('http://master-node:9870', user='hdfs')
added_film_ids = []
global COUNT
COUNT = 0
pending_film_ids = Queue()


def get_data(link, save_as=None):
    response = urllib.request.urlopen(link)
    data = response.read().decode('utf-8')

    # print(json.dumps(json.loads(data), indent=2))

    if (save_as != None):
        with open(save_as, 'w') as f:
            f.write(json.dumps(json.loads(data), indent=2))
    return json.loads(data)


def get_film_ids(year):
    film_ids = []
    print("getting film id...")
    for page in tqdm(range(1, 501)):
        for order in ('vote_average.desc', 'vote_count.desc', 'popularity.desc'):
            films = get_data(
                f"https://api.themoviedb.org/3/discover/movie?page={page}&sort_by={order}&year={year}&api_key={key}")
            for f in films['results']:
                if f['id'] not in added_film_ids:
                    added_film_ids.append(f['id'])
                    pending_film_ids.put(f['id'])

    print("Number of films: ", len(added_film_ids))
    return film_ids
# def update_weight(temp, films):
#     client = InsecureClient('http://master-node:9870', user='hdfs')

#     # with client.read("/user/hadoop/weight.csv", encoding = 'utf-8') as reader:
#     #     current_weight = pd.read_csv(reader)

#     temp['weight'] = temp['movie'].apply(lambda x: films[films['id'] == x]['popularity'])
#     weight_temp = temp[['actor1','actor2','weight']].groupby(['actor1','actor2']).mean().reset_index()
#     # current_weight['key'] = current_weight['actor1'].astype(str) +","+ current_weight['actor2'].astype(str)
#     # current_weight.drop(["actor1", 'actor2'],axis = 1, inplace = True)
#     # weight_dict = dict(zip(current_weight.key, current_weight.weight))

#     # weight_temp['key'] = weight_temp['actor1'].astype(str) +","+ weight_temp['actor2'].astype(str)

#     # weight_temp.drop(["actor1", 'actor2'],axis = 1, inplace = True)
#     # weight_dict_temp = dict(zip(weight_temp.key, weight_temp.weight))
#     # weight_dict.update(weight_dict_temp)

#     # new_weight = pd.DataFrame(weight_dict.items(),columns = ['key', 'weight'])
#     new_weight[['actor1','actor2']] = new_weight['key'].str.split(",", expand = True)
#     new_weight.drop("key", axis = 1, inplace = True)
#     cols = ["actor1", 'actor2', 'weight']
#     new_weight = new_weight[cols]
#     with client.write("/user/hadoop/weight.csv", encoding ="utf-8", overwrite=True) as writer:
#         new_weight.to_csv(writer)


def get_actors(actors):
    data = pd.DataFrame()
    for actor_id in actors:
        try:
            actor = get_data(
                f"https://api.themoviedb.org/3/person/{actor_id}?api_key={key}")
        except:
            print(f"Error of getting actor id {actor_id}.")
            continue

        data = pd.concat(
            [data, pd.Series(actor).to_frame().T], ignore_index=True)
    return data


def film_data():
    global COUNT
    films = pd.DataFrame()
    while True:
        if pending_film_ids.empty():
            continue
        
        id = pending_film_ids.get()
        temp = pd.DataFrame(columns=['actor1', 'actor2', 'weight'])
        print(f"getting film data: {id}")
        credit_link = f"https://api.themoviedb.org/3/movie/{id}/credits?api_key={key}"
        try:
            credit = get_data(credit_link)
            print('[INFO] Process 1')
        except:
            print(f"Error of getting movie id {id}.")
            continue
        actors = [a for a in credit['cast']
                    if a['known_for_department'] == "Acting"]
        to_num = min(len(actors), max(5, round(len(actors)*0.1)))
        main_actors = actors[:to_num]
        if len(main_actors) < 2:
            continue
        try:
            film = get_data(
                f"https://api.themoviedb.org/3/movie/{id}?api_key={key}")
        except:
            print(f"Error of getting movie id {id}.")
            continue
        for (a, b) in itertools.combinations(main_actors, 2):
            temp.loc[len(temp)] = sorted(
                [a['id'], b['id']]) + [max(film['popularity'],1e-5)]
        print("Writing to hdfs..")

        
        # with client.write(f'/user/hadoop/actor_pair.csv', encoding='utf-8') as writer:
        #     temp.to_csv(writer)
        # films = pd.concat(
        #     [films, pd.Series(film).to_frame().T], ignore_index=True)
        select_actor = [a['id']
                        for a in main_actors if a['id'] not in added_actors]
        if len(select_actor) > 0:
            actors = get_actors(select_actor)
            added_actors.extend(select_actor)
            #  APPEND TO CURRENT ACTOR DATA
            try:
                with client.write("/user/hadoop/actors.csv",  encoding='utf-8', append=True) as writer:
                    actors.to_csv(writer, header=False, index=False)
            except:
                with client.write("/user/hadoop/actors.csv",  encoding='utf-8') as writer:
                    actors.to_csv(writer, index=False)

        # with client.write("/user/hadoop/actors.csv",  encoding='utf-8', append=True) as writer:
        #     films.to_csv(writer, header=False, index=False)

        # WRITE NEW WEIGHT OF CURRENT MOVIE TO HDFS, NEW CSV FILE
        # temp['weight'] = temp['movie'].apply(
        #     lambda x: films[films['id'] == x]['popularity'])

        # weight_temp = temp[['actor1', 'actor2', 'weight']].groupby(
        #     ['actor1', 'actor2']).mean().reset_index()

        with client.write(f"{TEMP_WEIGHTS_DIR}/weight_{COUNT}.csv",  encoding='utf-8', overwrite=True) as writer:
            temp.to_csv(writer, header=False, index=False)
        os.system(f'hadoop fs -mv {TEMP_WEIGHTS_DIR}/weight_{COUNT}.csv {WEIGHTS_DIR}/')
        COUNT += 1

    return films


def main():
    year_start = 2022
    while year_start > 2015:
        threads = [
            Thread(target=get_film_ids, args=(year_start,)),
            Thread(target=film_data)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        year_start = year_start - 1

if __name__ == '__main__':
    main()
