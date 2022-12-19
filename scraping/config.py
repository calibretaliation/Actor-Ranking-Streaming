LOCAL_FOLDER  = ""

HDFS_FOLDER = ""

HADOOP_USER_NAME = "hadoop"

HADOOP_HOME = "/ust/local/hadoop/hadoop-3.3.4"

HADOOP_SWITCH_USER_COMMAND = ["sudo", "su", "-", f"{HADOOP_USER_NAME}"]

HDFS_PUT_COMMAND = [f"{HADOOP_HOME}/bin/hdfs", "dfs", "put", LOCAL_FOLDER, HDFS_FOLDER]

