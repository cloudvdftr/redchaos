from flask import Flask, render_template, request
import os
import subprocess
import uuid
import datetime
import sys
from flask_socketio import SocketIO, emit, send

CONFIG_FILE_PATH = "config"


class PodChart:

    def __init__(self):
        self.chart_pods = []

    def add_pod(self, pod_name):
        if pod_name is not None:
            checked_pod = self.__check_if_exists__(pod_name)
            if checked_pod is not None:
                checked_pod.add_value(1)
            else:
                self.chart_pods.append(ChartPod(pod_name))

    def remove_pod(self, pod_name):
        if pod_name is not None:
            checked_pod = self.__check_if_exists__(pod_name)
            if checked_pod is not None:
                checked_pod.add_value(-1)
                if checked_pod.value < 1:
                    self.chart_pods.remove(checked_pod)
            else:
                raise Exception("Specified Pod Doesn't Exist")

    def __check_if_exists__(self, pod_name):
        for chart_pod in self.chart_pods:
            if chart_pod.name == pod_name:
                return chart_pod
        return None


class PodHelper:
    def __init__(self):
        pass

    def strip_pod_name(self, pod_name):
        if pod_name is not None:
            index = pod_name.rfind('-')
            if index != -1:
                return str(pod_name)[:index]
            else:
                return str(pod_name)
        return pod_name


class ChartPod:

    def __init__(self, pod_name):
        self.name = pod_name
        self.value = 1

    def set_value(self, value):
        self.value = value

    def add_value(self, add=1):
        self.value += add


class TimeHelper:

    def __init__(self):
        pass

    # Returns the current time
    def get_current_time(self):
        time = str(datetime.datetime.now().time())
        index = time.rfind(".")
        return time[:index]


# Class that holds the configuration file information
class Config:

    def __init__(self):
        self.path = os.getcwd() + "/config"
        self.real_log_path = os.getcwd() + "/logs"

    def set_clusters(self, clusters):
        self.clusters = clusters

    def set_script_dir(self, working_dir):
        working_dir = self.__check_dir___(working_dir)
        self.working_dir = working_dir
        self.FILE_SCRIPT_PATH = working_dir + "monitor.sh"
        self.FILE_PATH = working_dir + "podstatus"
        self.TOTAL_FILE_PATH = working_dir + "totalpods"
        self.LOG_FILE_PATH = working_dir + "deadpods"
        self.PROJECT_NAMES_FILE_PATH = working_dir + "projectnames"
        self.ACCESS_SCRIPT_PATH = working_dir + "route.sh"
        self.ACCESS_FILE_PATH = working_dir + "route"
        self.SELECTED_CLUSTER_FILE_PATH = working_dir + "selected-cluster"
        self.SELECTED_PROJECT_FILE_PATH = working_dir + "selected-project"

    # Check if appropriate directory is given
    def __check_dir___(self, working_dir):
        if working_dir == None:
            return os.getcwd() + "/ocp/"
        my_dir = str(working_dir)
        if my_dir.startswith("/") == False:
            my_dir = "/" + my_dir
        if str(my_dir).endswith("/") == False:
            my_dir += "/"
        return my_dir


configurer = Config()
pod_list = PodChart()
pod_helper = PodHelper()
time_helper = TimeHelper()

# Sets the configurer with given parameters


def set_configurer(configurer):
    clusters = []
    working_dir = None
    clusters_parameter = "clusters="
    scripts_parameter = "scripts_working_dir="
    with open(configurer.path) as file:
        for line in file:
            line = line.replace(" ", "").lower()
            line = line.replace("\n", "")
            if line.startswith(clusters_parameter):
                line = line[len(clusters_parameter):]
                clusters = line.split(",")
                if clusters[0] == "" or clusters[0] == "\n":
                    clusters = []
            elif line.startswith(scripts_parameter):
                working_dir = line[len(scripts_parameter):]
                if working_dir == "\n":
                    working_dir = ""
    if len(clusters) > 0:
        if working_dir != None:
            configurer.set_script_dir(working_dir)
            configurer.set_clusters(clusters)
            return configurer
        else:
            try:
                raise Exception(
                    "Please Add Script Working Directory To Config File")
            except Exception as error:
                print(error)
                sys.exit(1)
    else:
        try:
            raise Exception("Please Add Clusters To Config File")
        except Exception as error:
            print(error)
            sys.exit(1)


# Starts before the app
def start_up():
    global configurer
    configurer = set_configurer(configurer)

    return Flask(__name__)


# Make sure to start up before setting the app!!!
app = start_up()

app.config['SECRET_KEY'] = "secret!"
socketio = SocketIO(app, async_mode='eventlet', async_handlers=True)

thread = None
threadList = []
kill_thread_list = []
modifiedTime = None
restartThread = False
cancel_killing = False
openNodes = 0
myNodeList = []
openValues = []
closeValues = []
GRAPH_SIZE = 20
labels = []
values = []
host_thread = None
project_modified_time = None
is_host_canceled = False
log_date = None


"""
@author Kaan Kocabas - Vodafone Turkey
"""
@app.route("/")
def main():
    title1 = "Running Pods"
    title2 = "Error Pods"
    return render_template('index.html', values=values, labels=labels, clusters=configurer.clusters, title1=title1, title2=title2,
                           async_mode=socketio.async_mode)


# Starts the monitoring process
def status_update_thread(uniqueId):
    global restartThread
    global threadList
    global configurer
    global host_thread
    first = True
    while True:
        if uniqueId not in threadList:
            break
        os.system("/usr/bin/sh " + configurer.FILE_SCRIPT_PATH)
        # If it is the first loop check for the host connections
        if first:
            hostId = str(uuid.uuid1())
            host_thread = hostId
        socketio.sleep(5)
        if first:
            # Start it as a thread
            socketio.start_background_task(host_connection, hostId)
            first = False
        socketio.sleep(10)


# Gets the selected cluster as parameter and updates the projects
@socketio.on('update projects')
def project_names_update(cluster):
    global threadList
    global configurer

    # Notify the frontend for the cluster change
    socketio.emit('cluster change', cluster)

    # Make sure there are no running tasks!!!
    restartThreads()

    if cluster == None:
        cluster = ""

    write_selected_cluster(cluster, configurer)

    run_project_names_script(configurer)

    project_list = get_project_names(configurer)

    # Notify the frontend for updated projects
    socketio.emit('projects updated', project_list)


# Writes the selected cluster to the selected_cluster_file for the scripts to work
def write_selected_cluster(cluster, configurer):
    selectedClusterFile = open(configurer.SELECTED_CLUSTER_FILE_PATH, 'w')
    selectedClusterFile.write(cluster)
    selectedClusterFile.close()


# Run the script for getting the project names
def run_project_names_script(configurer):
    os.system("/usr/bin/sh /ocp/projectnames.sh")
    f = open(configurer.SELECTED_PROJECT_FILE_PATH, "w")
    f.close()
    socketio.sleep(2)


# Get the project names and update the project names
def get_project_names(configurer):
    file = open(configurer.PROJECT_NAMES_FILE_PATH, 'r')
    project_list = []
    for line in file:
        if str(line).strip() != "NAME":
            project_list.append(str(line).strip())
    file.close()
    return project_list


# Resets the log file and the log area on the frontend
def set_logs():
    global configurer
    reset_log_date()
    socketio.emit('log clear')
    logFile = open(configurer.LOG_FILE_PATH, 'w')
    logFile.write("")
    logFile.close()


# Reset log_date so it would start a new log file for new operations
def reset_log_date():
    global log_date
    log_date = None


def add_to_log(pod_name, cluster, project, log_date, is_first):
    if pod_name is not None:

        if not check_log_date(log_date):
            set_log_console(cluster, project, log_date)

        real_log_file = set_real_log(cluster, project, log_date)
        line = time_helper.get_current_time() + " " + pod_name + " has been deleted\n"
        socketio.emit('log', line)
        real_log_file.write(line)
        real_log_file.close()

        socketio.sleep(0.2)


# Starts the logging operation
def get_logs(cluster, project, log_date):
    global configurer
    logFile = open(configurer.LOG_FILE_PATH, 'r')
    real_log_file = set_real_log(cluster, project, log_date)
    for line in logFile:
        # Notify frontend for the logs
        socketio.emit('log', line)
        # Write the logs to the log file with date
        real_log_file.write(line)
    real_log_file.close()
    logFile.close()
    socketio.sleep(0.2)


# Checks if it same log datet file has been created or not
def check_log_date(log_date):
    return os.path.exists(configurer.real_log_path + "/log_" + log_date)

# Creates a log file with log date for holding on to
def set_real_log(cluster, project, log_date):
    if not os.path.exists(configurer.real_log_path):
        os.makedirs(configurer.real_log_path)
    
    real_log_file = open(configurer.real_log_path +
                             "/log_" + log_date, 'a')

    if not check_log_date(log_date):
        real_log_file.write("SELECTED CLUSTER = " + cluster + "\n")
        real_log_file.write("SELECTED PROJECT = " + project + "\n")

    return real_log_file


def set_log_console(cluster, project, log_date):
    socketio.emit("log clear")
    socketio.emit("SELECTED CLUSTER = " + cluster + "\n")
    socketio.emit("SELECTED PROJECT = " + project + "\n")
    socketio.emit("DATE = " + log_date + "\n")


def kill_thread(unique_id, seconds, cluster, project, log_date):
    global openNodes
    global kill_thread_list
    global pod_list
    global pod_helper
    first_time = True
    while True:
        if unique_id not in kill_thread_list:
            break

        var = str(os.popen("/usr/bin/sh /ocp/command.sh").read())
        var = var.replace('"', '').replace(" ", "")
        first = var.rfind("pod") + 3
        second = var.rfind("deleted")
        if first != -1 or second != -1:
            deleted_pod = var[first:second]
            pod_list.remove_pod(pod_helper.strip_pod_name(deleted_pod))

        if openNodes > 0:
            openNodes -= 1

        # socketio.emit('pod updated', openNodes)
        # set_graph_values(openNodes)
        # set_second_graph_values(pod_list)
        socketio.start_background_task(
            add_to_log, deleted_pod, cluster, project, log_date, first_time)
        # socketio.start_background_task(get_logs, cluster, project, log_date)
        socketio.sleep(seconds)
        first_time = False


def restartThreads():
    global threadList
    global labels
    global values
    global kill_thread_list
    global openNodes
    openNodes = 0
    labels = []
    values = []
    threadList = []
    set_logs()
    kill_thread_list = []


# Sets the project and starts a thread for monitoring
@socketio.on('background thread')
def set_project(project):
    global thread
    global restartThread
    global threadList
    global configurer

    # Stop the tasks if there are any
    restartThreads()

    if project == None:
        project = ""

    # Write the selected project to the appropriate file
    selectedProFile = open(configurer.SELECTED_PROJECT_FILE_PATH, 'w')
    selectedProFile.write(project)
    selectedProFile.close()

    # Notify the frontend Project Changed
    socketio.emit("project change", project)

    # Make sure the frontend is set
    socketio.sleep(5)

    # Monitoring started show the visual chart
    socketio.emit('show chart')

    # Create two unique ids for two different threads to have control over the threads
    uniqueId1 = str(uuid.uuid1())
    threadList.append(uniqueId1)

    uniqueId2 = str(uuid.uuid1())
    threadList.append(uniqueId2)

    # Start the threads with the specified unique ids
    socketio.start_background_task(status_update_thread, uniqueId1)
    socketio.start_background_task(background_thread, uniqueId2)

    # Check the application to set the selection to disabled
    check_application()


# Working thread on the background emits an event with socketio
def background_thread(uniqueId):
    global modifiedTime
    global myNodeList
    global file
    global restartThread
    global threadList
    global configurer
    global pod_helper

    while True:
        if (uniqueId not in threadList):
            break

        # If the file has been modified
        if modifiedTime == None or modifiedTime != os.path.getmtime(configurer.FILE_PATH):
            global labels
            global values
            global openNodes
            global pod_list
            openNodes = 0
            # Empty the pod_list
            pod_list.chart_pods = []

            # In python open file every time to get notified not necessary in windows
            file = open(configurer.FILE_PATH, 'r')
            modifiedTime = os.path.getmtime(configurer.FILE_PATH)
            file.seek(0)
            for line in file:
                myList = line.split(' ')
                myList = list(filter(None, myList))  # fastest

                if len(myList) >= 3:
                    pod_name = pod_helper.strip_pod_name(myList[0])

                    if pod_name != "NAME":
                        if str(myList[2]).__contains__('Running'):
                            pod_list.add_pod(pod_name)
                            openNodes += 1

            socketio.emit('clear')
            socketio.emit('pod updated', openNodes)
            set_graph_values(openNodes)
            set_second_graph_values(pod_list)

        else:
            # Needed for cpu performance and letting other threads to run
            socketio.sleep(0.1)  # Sleep briefly
            continue

        file.close()


# Sets the chart values
def set_graph_values(open_nodes=0):
    global labels
    global values
    global time_helper
    labels.append(time_helper.get_current_time())
    values.append(open_nodes)
    labels = _format_(labels)
    values = _format_(values)
    socketio.emit('update chart', {
        "labels": labels,
        "values": values
    })


# Sets the second chart values
def set_second_graph_values(pod_list=[]):
    var = []
    for pod in pod_list.chart_pods:
        var.append({
            "name": pod.name,
            "value": pod.value
        })
    socketio.emit("update second chart", var)


# Formats the list to only show the specified size of values
def _format_(mylist=[]):
    global GRAPH_SIZE
    if len(mylist) > GRAPH_SIZE:
        mylist.pop(0)
        return _format_(mylist)
    else:
        return mylist


# Checks the route connections
@socketio.on('host connection')
def host_connection_socket():
    global host_thread
    host_thread = str(uuid.uuid1())
    host_connection(host_thread)


# Emits the hosts and their status
def host_connection(host_id):
    global configurer
    global host_thread

    if host_id == host_thread:
        myHostList = []
        hosts = open(configurer.ACCESS_FILE_PATH, 'r')
        for line in hosts:
            hostList = line.split(' ')
            hostList = list(filter(None, hostList))  # fastest
            if len(hostList) > 0 and not hostList[1].startswith('HOST'):
                myHostList.append(get_host_status(hostList[1]))
        hosts.close()
        socketio.emit('host updated', myHostList)


# Stops the host connection thread
@app.route('/cancelhost', methods=['DELETE'])
def cancel_host():
    global host_thread
    host_thread = None
    return {
        "status": 204
    }


# Checks the host status and returns the host and status in json format
def get_host_status(host):
    # Check the host status with curl max time out is 1 seconds!!!
    arch = subprocess.Popen("/usr/bin/curl --max-time 1 -I " + host + " | /usr/bin/awk '{print $2}'", shell=True,
                            stdout=subprocess.PIPE)
    a = arch.stdout.readline().strip().decode("utf-8")
    # a = str(os.popen("/usr/bin/curl --max-time 1 -I " + host + " | /usr/bin/awk '{print $2}'").read())
    # print("host is : " + a)
    if a == '302' or a == '200':
        status = 'OK'
    else:
        status = 'NOT'
    return {
        'host': host,
        'status': status
    }


# Stops the threads and restarts the application
@socketio.on('stop background')
def restart_application():
    restartThreads()
    socketio.emit("stop tasks")
    socketio.emit("enable selection", True)
    socketio.emit('pod updated', 0)
    set_graph_values(0)
    set_second_graph_values(PodChart())


# Finds the connection and starts the background thread
@socketio.on('connect')
def test_connect():
    global modifiedTime
    global myNodeList
    # After any connection made, make sure to open up the file and read again
    modifiedTime = None
    myNodeList = []


# Check if the application is ready for selection
@socketio.on('check application')
def check_application():
    global threadList
    global kill_thread_list
    if len(threadList) > 0 or len(kill_thread_list) > 0:
        socketio.emit("enable selection", False)
    else:
        socketio.emit("enable selection", True)


# Kills a pod every specified seconds until it is canceled
@socketio.on('kill pod')
def pod_kill(selection):
    global kill_thread_list
    global openNodes
    global log_date
    if len(kill_thread_list) == 0:
        unique_id = uuid.uuid1()
        kill_thread_list.append(unique_id)
        socketio.emit("py kill pod", selection)
        if log_date == None:
            log_date = str(datetime.datetime.now())
        socketio.start_background_task(
            kill_thread, unique_id, int(selection["seconds"]), selection["cluster"], selection["project"], log_date)


# Cancels killing the pods operation with DELETE and returns the status with POST methods
@app.route('/cancelkill', methods=['POST', 'DELETE'])
def cancel_killing_pods():
    global cancel_killing
    if request.method == 'POST':
        return {
            "cancel": cancel_killing,
            "status": 200
        }
    if request.method == 'DELETE':
        cancel_killing = True
        return {
            "data": "cancel killing pods",
            "status": 200
        }


# Tests the connection needed for other browsers to recognize!!!
@socketio.on('host connection testing')
def host_test():
    socketio.emit("host connection tested")


# Cancels killing needs to be activated with the other method to make sure all the browsers are notified
# DO NOT CHANGE!!!
@socketio.on('cancel kill pod')
def cancel_pod_kill():
    global kill_thread_list
    global cancel_killing
    cancel_killing = False
    kill_thread_list = []
    # Notify the frontend for the cancelation of the pods
    socketio.emit("py cancel kill pod")


# Run with socketio
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000)
