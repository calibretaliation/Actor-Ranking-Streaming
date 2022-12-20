LOCAL_FOLDER  = "/"

HDFS_FOLDER = "/"

HADOOP_HOME = "/usr/local/hadoop/hadoop-3.3.4"

HDFS_PUT_COMMAND = ["{}/bin/hdfs".format(HADOOP_HOME), "dfs", "put", LOCAL_FOLDER, HDFS_FOLDER]

HDFS_RM_COMMAND = ["{}/bin/hdfs".format(HADOOP_HOME), "dfs", "rm", ""]
