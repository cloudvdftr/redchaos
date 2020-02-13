Links:
https://developers.redhat.com/blog/2018/08/13/install-python3-rhel/

########### MODULES NEEDED ###########
--> yum -y install rh-python36
--> pip install flask
--> pip install flask-socketio
--> pip install eventlet
--> pip install cryptography

########### HOW TO CREATE USERNAME AND PASSWORD ###########
--> Create a file named data
--> Write the username and password as below
    username="username"
    password="password"
--> run generate_key.py
--> run encrypt_file.py
--> You should be able to see data.enc and data should be removed.
--> NOTE: DO NOT LOSE THE KEY MAKE SURE TO STORE IT SOMEWHERE SAFE AND ADD IT TO THE SAME FOLDER
--- WHEN THE APPLICATION IS GOING TO BE USED 
--> IF YOU LOSE THE KEY FILE PLEASE START FROM THE BEGINNING