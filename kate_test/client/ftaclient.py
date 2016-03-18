# FTA Client with interactive command window
import os
import sys
sys.path.insert(0,'..')
from rtp import *

# create a reliable connection with the FTA server
# return socket
def connect(host, port, rwnd):
	try:
		sock = RTPSocket()
		sock.rwnd = rwnd
		port = int(port)
		sock.connect((host,port))
		print "Connected"
		return sock
	except:
		print('Error: Unable to connect to server.')
		raise
		sys.exit(1)
		

# download file1 from server and upload file2 to the server through the same RTP connection
# use multithreading or other way to support multiple simultaneous RTP connections
# this is extra credit now
def get_post(file1, file2, sock, host, port, rwnd):
	pass


# download file from server
def get(filename, sock, host, port, rwnd):
	
	# send filename to server
	sock.send(filename, (host, port))
	ofile = open(filename, "wb") # open in write bytes mode
	while 1:
		# receive response from server
		data, addr = sock.recv()
		if data == "File not found.":
			print "Error: File not found."
			ofile.close()
			os.remove(filename)
			break
		elif data == "FILE FINISHED SENDING":
			break
		elif data:
			# write the file
			ofile.write(data)				
		else:
			continue
	ofile.close()

def main(argv):
	# arguments should be H:P W
	if len(argv) != 2:
		print "Wrong number of arguments.\npython ftaclient.py $HOST:$PORT $RWND"
		sys.exit(1)


	arg0 = argv[0].split(":")
	host = arg0[0]
	port = int(arg0[1])
	rwnd = int(argv[1])

	disconnect = False
	sock = connect(host, port, rwnd)

	while disconnect == False:
		command = raw_input("> ")
		if command == "disconnect":
			disconnect = True
			# disconnect from the server gracefully
			# todo send FIN to server
			try:
				sock.close()
			except:
				disconnect = True
				#CHANGE THIS BACK 	disconnect = False

		elif "get-post" in command:
			# arguments should be F G
			# F: download file F from the server
			# G: upload file G to the server through same RTP connection
			cmd_list = command.split(" ")
			if len(cmd_list) != 3:
				print "Wrong number of arguments for get-post (expected 2)"
				continue
			f = cmd_list[1]
			g = cmd_list[2]
			try:
				get_post(f,g, sock, host, port, rwnd)
			except:
				print "Error downloading or uploading file."

		elif "get" in command:
			# argument should be F
			# F: download file F from the server
			cmd_list = command.split(" ")
			if len(cmd_list) != 2:
				print "Wrong number of arguments for get (expected 1)"
				continue
			f = cmd_list[1]
			try:
				get(f, sock, host, port, rwnd)
			except:
				print "Error downloading file."
				raise # for debugging
		else:
			print "Invalid command."

	sys.exit(1)
  

if __name__ == "__main__":
    main(sys.argv[1:])

