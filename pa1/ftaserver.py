# FTA Server
from rtp import *
import os
import sys
import time


# download file1 from client and upload file2 to client in same RTP connection
# this is extra credit now
def get_post(file1, file2, sock, host, port, rwnd):
	pass


# upload file to client
# called whenever filename is received from the server
def post(filename, sock, host, port, rwnd):
	# check if file exists
	files = [f for f in os.listdir(".") if os.path.isfile(f)]
	print files
	print sock.rwnd
	if filename not in files:
		error_msg = "File not found."
		sock.send(error_msg, (host, port))
	else:
		send_file = open(filename, "rb") #rb to read in binary mode
	try:
		# send file to client
		msg = send_file.read(rwnd) # read a portion of the file
		while msg:
			sock.send(msg, (host, port))
			msg = send_file.read(rwnd)
		send_file.close() # close the file
		print "sent file to client"
	except:
		send_file.close() # make sure file is closed
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
				# send the file (or error msg) to client
				post(filename, sock, dest_host, dest_port, rwnd)				
			else:
				continue
	except:
		print "Error"
		raise # for debugging
 

if __name__ == "__main__":
    main(sys.argv[1:])