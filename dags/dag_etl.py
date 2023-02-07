import random
import pytz
from datetime import datetime, timedelta

from airflow.decorators import dag, task

### DAG FLOW ###
@dag(
    start_date=datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')),
    schedule_interval="@daily",
    catchup=False,
    tags=['pagerank'],
)
def dag_pagerank():
    ### TASK 1 ###
    @task.virtualenv(
        task_id = 'films_crawl', requirements=["urllib", "urllib", "itertools", "pandas", "tqdm", "numpy", "ast", "hdfs"], system_site_packages=False
        )
    def films_crawl():
        from urllib import request
        import urllib
        import itertools
        import pandas as pd
        from tqdm import tqdm
        import numpy as np
        import ast
        from hdfs import InsecureClient
        def get_data(link, save_as=None):
            response = urllib.request.urlopen(link)
            data = response.read().decode('utf-8')

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
        
    # ### TASK 2 ###
    # @task.virtualenv(
    #     task_id = 'hdfs_put', requirements=["subprocess", "config", "time", "sys", "watchdog.observers", "watchdog.events", "pyarrow"], system_site_packages=False
    #     )
    # def hdfs_put(a2):
    #     import subprocess
    #     import config
    #     import time 
    #     import sys
    #     from watchdog.observers import Observer
    #     from watchdog.events import PatternMatchingEventHandler
    #     from pyarrow import fs
        
    #     hdfs = fs.HadoopFileSystem(host, port, user="nhat-node")

    #     def hdfs_put(local_file_path, hdfs_file_path):
    #         command = config.HDFS_PUT_COMMAND
    #         if local_file_path is not None:
    #             command[-2] = local_file_path
    #         if hdfs_file_path is not None:    
    #             command[-1] = hdfs_file_path
    #         subprocess.Popen(["echo", str(command)])
    #         return command

    #     def hdfs_delete(hdfs_file_path):
    #         command = config.HDFS_RM_COMMAND
    #         if hdfs_file_path is not None:    
    #             command[-1] = hdfs_file_path
    #         subprocess.Popen(["echo", str(command)])
    #         return command

    #     class Event(PatternMatchingEventHandler):
    #         def on_created(self, event):
    #             hdfs_put(local_file_path = event.src_path, hdfs_file_path = config.HDFS_FOLDER)
    #             print(f"{event.src_path} created")
    #         def on_modified(self, event):
    #             hdfs_put(local_file_path = event.src_path, hdfs_file_path = config.HDFS_FOLDER)
    #             print(f"{event.src_path} modified")
    #         def on_moved(self, event):
    #             hdfs_put(local_file_path = event.src_path, hdfs_file_path = config.HDFS_FOLDER)
    #             print(f"{event.src_path} moved")
    #         def on_deleted(self, event):
    #             hdfs_file_path = config.HDFS_FOLDER + event.src_path
    #             hdfs_delete(hdfs_file_path = hdfs_file_path)
    #             print(f"{event.src_path} deleted")       
                
    #     #Init an observer before calling this function        
    #     def watch_folder(observer, path = "/home/hadoop/"):
    #         event_handler = Event(patterns=["*.json"])
    #         observer.schedule(event_handler, path, recursive=True)
    #         observer.start()
    #     def stop_watch_folder(observer):
    #         observer.stop()
    #         observer.join()
    
    # ### TASK 3 ###
    # @task.virtualenv(
    #     task_id='send_weight', requirements=["socket", "threading", "time", "pandas", "watchdog.observers", "watchdog.events", "pyarrow"], system_site_packages=False
    #     )
    # def send_weight(a3):
    #     import socket
    #     from threading import *
    #     import time
    #     import pandas as pd
    #     from watchdog.observers import Observer
    #     from watchdog.events import PatternMatchingEventHandler
    #     from pyarrow import fs
        
    #     host = "192.168.2.20"
    #     port = 4321
    #     print(host,"://",port)

    #     hdfs = fs.HadoopFileSystem(host, port, user="hdfs")

    #     weight_temp = pd.read_csv("/home/calibretaliation/LinkedIn-Analysis/popularity_weight.csv")

    #     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #     s.bind((host, port))
    #     s.listen(1)
    #     print('WAITING FOR CLIENT')

    #     try:
    #         while True:
    #             conn, addr = s.accept()
    #             print('CONNECTED:', addr)
    #             try:
    #                 for i, line in weight_temp.iterrows():
    #                     data = f"{line[0]},{line[1]},{line[2]}" +"\n"
    #                     conn.send(bytes(data, 'utf-8'))
    #                     time.sleep(1)
    #                     print(data)
    #                 conn.close()
    #                 print("CLOSED")
    #             except socket.error: pass
    #     finally:
    #         s.close()
        
    # ### TASK 4 ###
    # @task(task_id = 'LAP')
    # def LAP(a4):
    #     pass
    
    ### TASK 2 ###
    @task(task_id = 'page_rank', requirements=["pyspark", "hdfs"], system_site_packages=False)
    def page_rank(a5):
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
          
    ### TASK 3 ###
    @task(task_id = 'visualize_to_web')
    def visualize_to_web(a6):
        pass
    
    task1 = films_crawl()
    task2 = hdfs_put(task1)
    task3 = send_weight(task2)
    task4 = LAP(task3)
    task5 = page_rank(task4)
    visualize_to_web(task5)
    
dag = dag_pagerank()
