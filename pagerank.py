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
