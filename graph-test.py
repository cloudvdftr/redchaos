from flask import Flask, render_template
from flask_socketio import SocketIO, emit, send
import time
import datetime
import random
import uuid
import json


class DataSet:

    def __init__(self, name, labels, values):
        self.name = name
        self.labels = labels
        self.values = self.__get_values__(list(values), list(labels))
        self.color = self.__get_random_color__()

    def __get_values__(self, values, labels):
        if len(values) <= 0 and len(labels) > 0:
            return self.__add_to_values__(values, labels)
        return values

    def __add_to_values__(self, values, labels):
        values.append(0)
        if len(values) < len(labels):
            return self.__add_to_values__(values, labels)
        return labels

    def change_color(self, color):
        self.color = color

    def set_labels(self, labels):
        self.labels = labels

    def append_to_labels(self, label):
        self.labels.append(label)

    def set_values(self, values):
        self.values = values

    def append_to_values(self, value):
        self.values.append(value)

    def __get_random_color__(self):
        return "rgb(" + str(random.randint(0, 256)) + "," + str(random.randint(0, 256)) + "," + str(random.randint(0, 256)) + ")"

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


app = Flask(__name__)

app.config['SECRET_KEY'] = "secret!"
socketio = SocketIO(app)

GRAPH_SIZE = 20

data_sets = [DataSet(str(uuid.uuid1()), [], []),
             DataSet(str(uuid.uuid1()), [], [])]

labels = []

"""
@author Kaan Kocabas - Vodafone Turkey
"""
@app.route("/")
def main():
    return render_template('graph-test.html', async_mode=socketio.async_mode)


def get_datasets():
    global data_sets
    data_sets_json = []
    for data in data_sets:
        if data != None:
            my_data = {
                "name": data.name,
                "labels": data.labels,
                "values": data.values,
                "color": data.color
            }
            data_sets_json.append(my_data)
    return data_sets_json


@app.route("/data", methods=["POST"])
def add_data():
    global labels
    global data_sets

    for data_set in data_sets:
        data_set.append_to_values(random.randint(1, 5))

    labels.append(get_current_time())
    labels = _format_(labels)
    return {
        "labels": labels,
        "datasets": [
            get_datasets()
        ]
    }


@app.route("/project", methods=["POST"])
def add_project():
    global data_sets
    global labels
    ds = DataSet(str(uuid.uuid1()), labels, [])
    data_sets.append(ds)
    return {
        "labels": labels,
        "datasets": [
            get_datasets()
        ]
    }


@app.route("/color", methods=["GET"])
def get_random_color():
    ds = DataSet("", [], [])
    return ds.color


def _format_(mylist=[]):
    global GRAPH_SIZE
    if len(mylist) > GRAPH_SIZE:
        mylist.pop(0)
        return _format_(mylist)
    else:
        return mylist


def get_current_time():
    time = str(datetime.datetime.now().time())
    index = time.rfind(".")
    return time[:index]


# Run with socketio
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000)
