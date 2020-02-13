import os

current_path = os.path.dirname(os.path.realpath(__file__)) + "/"

var = str(os.popen('python ' + current_path + "decrypt_file.py").read())

var = var.replace('"', '')
var = var.replace("'", "")
arr = var.split("\n")

username_str = str(arr[0])
password_str = str(arr[1])
username = username_str[username_str.find("=") + 1:]
password = password_str[password_str.find("=") + 1:]

# print(username)
# print(password)
