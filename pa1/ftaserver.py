# FTA Server

import sys

def main(argv):

	# arguments should be port, rwnd
	if len(argv) != 2:
		print('Wrong number of arguments.\npython ftaclient.py $PORT $RWND')
        sys.exit(1)

	port = argv[0]
	rwnd = argv[1]
 

if __name__ == "__main__":
    main(sys.argv[1:])