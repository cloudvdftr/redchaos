from cryptography.fernet import Fernet
import os

path_prefix = os.path.dirname(os.path.realpath(__file__)) + "\\"

with open(path_prefix + "key", "wb") as file:
    file.write(Fernet.generate_key())