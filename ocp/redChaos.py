import os
import shutil
import random
import sys
import subprocess
import datetime

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
    
os.popen('/usr/bin/oc login ' + cluster +
          ' --username=' + username + ' --password=' + password)

os.popen('/usr/bin/oc project ' + project)

subprocess.check_output(
    " /usr/bin/oc get pods | /usr/bin/grep Running | /usr/bin/awk '{print $1}' | /usr/bin/grep -v NAME > /ocp/runningpods", shell=True)
# subprocess.check_output(" /usr/bin/oc get pods | /usr/bin/grep Running | /usr/bin/awk '$4 < 100'  | /usr/bin/awk '{print $1}' | /usr/bin/grep -v NAME > /ocp/runningpods", shell=True);
subprocess.check_output(
    " /usr/bin/oc get pods | /usr/bin/grep Running | /usr/bin/awk '$4 < 100' | /usr/bin/awk '{print $1}' | /usr/bin/grep -v NAME > /ocp/podlist", shell=True)
subprocess.check_output(
    " /usr/bin/oc project | /usr/bin/awk '{print $3 }' > /ocp/projectname", shell=True)
os.popen('/usr/bin/echo " Total pod number: `/usr/bin/cat /ocp/podlist | /usr/bin/wc -l` " > /ocp/totalpod ')
subprocess.check_output(" /usr/bin/oc get pods > /ocp/podstatus", shell=True)
# subprocess.check_output(" /usr/bin/oc get pods | /usr/bin/grep Running | /usr/bin/awk '$4 < 100' > /ocp/podstatus", shell=True);
subprocess.check_output(" /usr/bin/oc get route  > /ocp/route", shell=True)


#os.system('oc get pods | awk "{{ print $1 }}"  > /ocp/podlist')
filename = '/ocp/runningpods'
file2 = '/ocp/deadpods'
#os.system('/usr/bin/oc delete pod mysql-2-ngccg -n test-1')
#with open(filename) as f:
#       mylist=list(filter(None,mylist))
#       print(mylist)
#       print(random.choice(mylist))
with open(filename) as f:
    lines = f.readlines()
    pod = random.choice(lines)
    #print (pod)
    #print(random.choice(lines))
    cmd = "/usr/bin/oc delete pod " + pod
    f = open(file2, "a")
    now = datetime.datetime.now()
   # print ("Current date and time : ")
   # print (now.strftime("%Y-%m-%d %H:%M:%S"))
    f.write(now.strftime("%Y-%m-%d %H:%M:%S")+' ' + cmd)
    os.system(cmd)
    subprocess.check_output(
        " /usr/bin/oc get pods > /ocp/podstatus", shell=True)
