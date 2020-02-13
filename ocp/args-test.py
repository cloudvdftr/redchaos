import sys
import getopt


def main(argv):
    
    username = ""
    password = ""
    
    try:
        opts, args = getopt.getopt(argv, "h:u:p:", ["username=", "password="])
    except getopt.GetoptError:
        print('args-test.py -u <username> -p <password>')
        sys.exit(2)
    
    if len(opts) == 0:
        print('args-test.py -u <username> -p <password>')
        sys.exit(1)

    for opt, arg in opts:
        if opt == "-h":
            print('args-test.py -u <username> -p <password>')
            sys.exit(1)
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg

    print("username is ", username)
    print("password is ", password)


if __name__ == "__main__":
    main(sys.argv[1:])
