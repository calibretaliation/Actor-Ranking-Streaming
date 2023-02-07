import os
from threading import Thread

crawler_thread = Thread(target=os.system, args=('python3 film_crawler.py',))
pagerank_thread = Thread(target=os.system, args=('$SPARK_HOME/bin/spark-submit --master yarn --deploy-mode client pagerank.py',))
web_thread = Thread(target=os.system, args=('python3 pagerank_to_web.py',))

crawler_thread.start()
pagerank_thread.start()
web_thread.start()

crawler_thread.join()
pagerank_thread.join()
web_thread.join()