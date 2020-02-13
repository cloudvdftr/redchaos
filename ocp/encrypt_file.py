from cryptography.fernet import Fernet
import sys
import os

try:
    path_prefix = os.path.dirname(os.path.realpath(__file__)) + "\\"
    with open(path_prefix + "key", "rb") as file:
        key = file.read()
    f = Fernet(key)
    try:
        with open(path_prefix + "data", "r") as file:
            data = file.read()
        try:
            os.remove(path_prefix + "data")
            encoded = data.encode()
            with open(path_prefix + "data.enc", "wb") as file:
                file.write(f.encrypt(encoded))
        except Exception as error:
            print(error)
            sys.exit(1)
    except FileNotFoundError as error:
        try:
            raise Exception("data file is not found!")
        except Exception as error:
            print(error)
            sys.exit(1)
except FileNotFoundError as error:
    try:
        raise Exception("key file is not found!")
    except Exception as error:
        print(error)
        sys.exit(1)