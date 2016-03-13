# FTA Server
from rtp import *
import os
import sys
import time


# download file1 from client and upload file2 to client in same RTP connection
def get_post(file1, file2, sock, host, port):
	pass


# upload file to client
def post(file, sock, host, port):
	# check if file exists
	files = [f for f in os.listdir(".") if os.path.isfile(f)]
	print files
	if file not in files:
		send_file = "File not found."
	else:
		send_file = files[file]
	try:
		# send file to client
		sock.send(send_file, (host, port))
	except:
		print "Error: Unable to send file."


def main(argv):

	# arguments should be port, rwnd
	if len(argv) != 2:
		print "Wrong number of arguments.\npython ftaclient.py $PORT $RWND"
		sys.exit(1)

	port = int(argv[0])
	rwnd = argv[1]
	host = '127.0.0.1'

	# create socket and bind to port
	try:
		sock = RTPSocket()
		sock.bind((host, port))
		sock.accept()

		# wait for response from client
		while 1:
			data,addr = sock.recv()
			if data:
				dest_host = addr[0]
				dest_port = addr[1]
				filename = data
				# send error message if file does not exist
				post(filename, sock, dest_host, dest_port)				
			else:
				continue
	except:
		print "Error"
		raise # for debugging
 

if __name__ == "__main__":
    main(sys.argv[1:])