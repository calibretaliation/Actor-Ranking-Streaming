import urllib.request
import json
import itertools
import pandas as pd
from tqdm import tqdm
import numpy as np
import ast
from hdfs import InsecureClient


def get_data(link, save_as=None):
    response = urllib.request.urlopen(link)
    data = response.read().decode('utf-8')

    # print(json.dumps(json.loads(data), indent=2))

    if (save_as != None):
        with open(save_as, 'w') as f:
            f.write(json.dumps(json.loads(data), indent=2))
    return json.loads(data)


key = '8c0c786aba77a3ff00ebb47ca9fa3b8f'
TEMP_WEIGHTS_DIR = '/user/hadoop/temp_weight'
WEIGHTS_DIR = '/user/hadoop/weight'


def get_film_ids(year_start=2019, year_end=2023):
    film_ids = []
    print("getting film id...")
    for page in tqdm(range(1, 501)):
        for year in range(year_start, year_end):
            for order in ('vote_average.desc', 'vote_count.desc', 'popularity.desc'):
                films = get_data(
                    f"https://api.themoviedb.org/3/discover/movie?page={page}&sort_by={order}&year={year}&api_key={key}")
                film_ids.extend([f['id'] for f in films['results']])
    film_ids = list(set(film_ids))

    print("Number of films: ", len(film_ids))
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


def film_data(film_ids):
    films = pd.DataFrame()
    for id in tqdm(film_ids[0]):
        temp = pd.DataFrame(columns=['actor1', 'actor2', 'weight'])
        print(f"getting film data: {id}")
        credit_link = f"https://api.themoviedb.org/3/movie/{id}/credits?api_key={key}"
        try:
            credit = get_data(credit_link)
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
                [a['id'], b['id']]) + [film['popularity']]
        print("writing to hdfs..")

        client = InsecureClient('http://master-node:9870', user='hdfs')
        # with client.write(f'/user/hadoop/actor_pair.csv', encoding='utf-8') as writer:
        #     temp.to_csv(writer)
        # films = pd.concat(
        #     [films, pd.Series(film).to_frame().T], ignore_index=True)

        # #  APPEND TO CURRENT MOVIE DATA
        # with client.write("/user/hadoop/movie.csv",  encoding='utf-8', append=True) as writer:
        #     films.to_csv(writer, header=False, index=False)

        # WRITE NEW WEIGHT OF CURRENT MOVIE TO HDFS, NEW CSV FILE
        # temp['weight'] = temp['movie'].apply(
        #     lambda x: films[films['id'] == x]['popularity'])

        # weight_temp = temp[['actor1', 'actor2', 'weight']].groupby(
        #     ['actor1', 'actor2']).mean().reset_index()

        with client.write(f"{TEMP_WEIGHTS_DIR}/weight_{id}.csv",  encoding='utf-8') as writer:
            temp.to_csv(writer, index=False)
        os.system(
            f'hadoop fs -mv {TEMP_WEIGHTS_DIR}/f_{no}.csv {WEIGHTS_DIR}/')

    return films


if __name__ == '__main__':
    year_start = 2017
    while year_start > 2015:
        film_ids = []
        film_ids.append(get_film_ids(year_start, 2023))
        films = film_data(film_ids)
        year_start = year_start - 1
