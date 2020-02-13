import os, subprocess

current_path = os.path.dirname(os.path.realpath(__file__)) + "/"

var = str(os.popen('python ' + current_path + "decrypt_file.py").read())

var = var.replace('"', '')
var = var.replace("'", "")
arr = var.split("\n")

username_str = str(arr[0])
password_str = str(arr[1])
username = username_str[username_str.find("=") + 1:]
password = password_str[password_str.find("=") + 1:]

with open('/ocp/selected-cluster') as f:
    cluster = f.readline()
with open('/ocp/selected-project') as f2:
    project = f2.readline()
os.system('/usr/bin/oc login ' + cluster +
          ' --username=' + username + ' --password=' + password)

os.system('/usr/bin/oc project ' + project)