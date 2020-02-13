from flask import Flask, render_template
from flask_socketio import SocketIO, emit, send
import os

clusters = []


def get_clusters(path):
    clusters = []
    clusters_parameter = "clusters="
    with open(path) as file:
        for line in file:
            line = line.replace(" ", "").lower()
            if line.startswith(""):
                line = line[len(clusters_parameter):]
                clusters = line.split(",")
                if clusters[0] == "":
                    clusters = []
    return clusters


def start_up():
    global clusters
    clusters = get_clusters(os.getcwd() + "/config")
    print(len(clusters))
    print(clusters)
    if len(clusters) > 0:
        return Flask(__name__)
    else:
        try:
            raise Exception("Please Add Clusters To Config File")
        except Exception as error:
            print(error)


app = start_up()

app.config['SECRET_KEY'] = "secret!"
socketio = SocketIO(app)


"""
@author Kaan Kocabas - Vodafone Turkey
"""
@app.route("/")
def main():
    global clusters
    return render_template('conf-test.html', clusters=clusters, async_mode=socketio.async_mode)


# Run with socketio
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000)
