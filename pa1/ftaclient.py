# FTA Client with interactive command window

import sys

# create a reliable connection with the FTA server
def connect(host, port, rwnd):
	pass


# download file1 from server and upload file2 to the server through the same RTP connection
def get_post(file1, file2):
	pass


# download file from server
def get(file):
	pass


def main(argv):

	# arguments should be H:P W
	if len(argv) != 2:
		print('Wrong number of arguments.\npython ftaclient.py $HOST:$PORT $RWND')
        sys.exit(1)

    arg0 = argv[0].split(":")
    host = arg0[0]
    port = arg0[1]
    rwnd = argv[1]

	disconnect = False
	connect()

	while disconnect == False:
		command = raw_input("> ")
		if command == disconnect:
			disconnect = True
		elif "get-post" in command:
			# arguments should be F G
			# F: download file F from the server
			# G: upload file G to the server through same RTP connection
			get_post(f,g)
		elif "get" in command:
			# argument should be F
			# F: download file F from the server
			get(f)
		else:
			print "Invalid command."

	sys.exit(1)
  

if __name__ == "__main__":
    main(sys.argv[1:])

