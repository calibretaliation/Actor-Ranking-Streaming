from datetime import datetime, timedelta
from airflow import DAG
import pandas as pd

from airflow.operators.python import PythonOperator

def film_crawler():
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
    added_actor = []


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
            print("Writing to hdfs..")

            client = InsecureClient('http://master-node:9870', user='hdfs')
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
                with client.write("/user/hadoop/actors.csv",  encoding='utf-8', append=True) as writer:
                    actors.to_csv(writer, header=False, index=False)

            # with client.write("/user/hadoop/actors.csv",  encoding='utf-8', append=True) as writer:
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


def pagerank():
    from pyspark import SparkContext
    from pyspark.streaming import StreamingContext
    from hdfs import InsecureClient


    MONITOR_DIR = 'hdfs:///user/hadoop/weight/'
    BATCHING_TIME = 20
    N_THREADS = 4
    N_ITERS = 3
    MOVING_AVERAGE_COEF = 0.5
    WINDOW_LENGTH = 60
    SLIDE_INTERVAL = 30

    NODENAME = 'http://master-node:9870'
    OUT_PATH = '/user/hadoop/output_ranks.csv'


    def message_to_links(message):

        # print(f'[INFO] Receive message {message}')

        message = message.strip()
        delimeter = ',' if ',' in message else None
        message = message.split('\n')
        message = [line.split(delimeter) for line in message]
        ret = [(int(s), int(d), float(w)) for s, d, w in message]

        # print(f'[INFO] Converted to {ret}')

        return ret


    def link_to_2directed_edges(link):
        s, d, w = link
        return [(s, (d, w)), (d, (s, w))]
        # TODO src -> dst


    def combine_newly_or_updated_edges(new_edges, old_state):

        new_state = ([], [])

        # old_state = [[d, d, ...], [w, w, ...]]
        if old_state is None:
            old_state = ([], [])

        # make a copy of old state
        for d, w in zip(*old_state):
            new_state[0].append(d)
            new_state[1].append(w)

        # new_edges = [(d, w), (d, w), ...]
        for d, w in new_edges:
            if d not in new_state[0]:
                new_state[0].append(d)
                new_state[1].append(w)
            else:
                index = new_state[0].index(d)
                new_state[1][index] = (1 - MOVING_AVERAGE_COEF) * \
                    new_state[1][index] + MOVING_AVERAGE_COEF * w

        # print('[INFO] New state:', new_state)

        return new_state


    def egdes_to_transitions(edges):
        s, ((destinations, weights), rank) = edges

        ret = []

        for d, w in zip(destinations, weights):
            ret.append((d, rank * w/sum(weights)))

        return ret


    def init_rank(edges):
        s, _ = edges
        return s, 1.0


    def export_result(rdd):
        print('[INFO] Printing')
        buf = []
        for vertex, rank in rdd.collect():
            buf.append(f'{vertex},{rank}')
        CLIENT = InsecureClient(NODENAME, user='hdfs')
        with CLIENT.write(OUT_PATH, encoding="utf-8", overwrite=True) as writer:
            print('\n'.join(buf), file=writer)
        print('\n'.join(buf))
        print('[INFO] Done')


    def main():

        sc = SparkContext(f'local[{N_THREADS}]', 'PageRank')
        ssc = StreamingContext(sc, BATCHING_TIME)
        ssc.checkpoint("checkpoint")

        messages = ssc.textFileStream(MONITOR_DIR)

        edges = messages\
            .flatMap(message_to_links)\
            .flatMap(link_to_2directed_edges)\
            .updateStateByKey(combine_newly_or_updated_edges)

        ranks = edges.map(init_rank)

        for k in range(N_ITERS):

            contribs = edges\
                .join(ranks)\
                .flatMap(egdes_to_transitions)

            if k == 0 and WINDOW_LENGTH is not None and SLIDE_INTERVAL is not None:
                ranks = contribs.reduceByKeyAndWindow(
                    lambda contrib1, contrib2: contrib1 + contrib2, WINDOW_LENGTH, SLIDE_INTERVAL)
            else:
                ranks = contribs.reduceByKey(
                    lambda contrib1, contrib2: contrib1 + contrib2)

            total = ranks.map(lambda x: (1, (x[1], [x[0]])))\
                .reduceByKey(lambda x, y: (x[0] + y[0], x[1] + y[1]))\
                .flatMap(lambda x: [(v, x[1][0]) for v in x[1][1]])

            ranks = ranks.join(total).map(lambda x: (x[0], x[1][0] / x[1][1]))

        ranks.foreachRDD(export_result)
        # ranks.pprint()

        ssc.start()
        ssc.awaitTermination()


    if __name__ == '__main__':
        main()


def pagerank_to_web():
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
    added_actor = []


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
            print("Writing to hdfs..")

            client = InsecureClient('http://master-node:9870', user='hdfs')
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
                with client.write("/user/hadoop/actors.csv",  encoding='utf-8', append=True) as writer:
                    actors.to_csv(writer, header=False, index=False)

            # with client.write("/user/hadoop/actors.csv",  encoding='utf-8', append=True) as writer:
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

dag = DAG(
    'test_context',
    default_args={
        'email': ['labidien2001@gmail.com'],
        'email_on_failure': True,
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    },
    start_date=datetime.now(),
    schedule_interval="@daily",
    catchup=False,
    tags=['pagerank'])


film_crawler_operator = PythonOperator(
    task_id='film_crawler',
    python_callable=film_crawler,
    dag=dag
)

pagerank_operator = PythonOperator(
    task_id='pagerank',
    python_callable=pagerank,
    dag=dag
)

pagerank_to_web_operator = PythonOperator(
    task_id='pagerank_to_web',
    python_callable=pagerank_to_web,
    dag=dag
)

film_crawler_operator >> pagerank_operator >> pagerank_to_web_operator