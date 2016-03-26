"""Server side of File Transfer Application."""
import os
import sys
import time
import threading
sys.path.insert(0,'..')
from rtp import *

lock = threading.Lock()

def get_post(file1, file2, sock, host, port, rwnd):
	"""Downloads file1 from cient and uploads file2 to client in same RTP connection."""
	#need to implement threading here

	upload_thread = threading.Thread(target = uploadFile, args = (file1, sock, host, port, rwnd))
	upload_thread.start()
	upload_thread.join()

	download_thread = threading.Thread(target = downloadFile, args = (file2, sock, host, port, rwnd))
	download_thread.start()
	upload_thread.join()
	#uploadFile(file1, sock, host, port, rwnd)
	#downloadFile(file2, sock, host, port, rwnd)
	#pass

def get(filename, sock, host, port, rwnd):
	upload_thread = threading.Thread(target = uploadFile, args = (filename, sock, host, port, rwnd))
	upload_thread.start()
	upload_thread.join()

def uploadFile(filename, sock, host, port, rwnd):
	"""Uploads file to client. Called whenever filename is received from server."""
	# check if file exists
	files = [f for f in os.listdir(".") if os.path.isfile(f)]
	print files
	print sock.rwnd
	if filename not in files:
		error_msg = "ERROR: FILE NOT FOUND"
		sock.send(error_msg, (host, port))
		send_file = None
	else:
		send_file = open(filename, "rb") #rb to read in binary mode
	try:
		# send file to client
		msg = send_file.read(rwnd) # read a portion of the file
		while msg:
			sock.send(msg, (host, port))
			msg = send_file.read(rwnd)
		send_file.close() # close the file
		sock.send("FILE FINISHED SENDING", (host, port))
		print "sent file to client"
	except:
		if send_file:
			send_file.close() # make sure file is closed
		print "Error: Unable to send file."

def downloadFile(filename, sock, host, port, rwnd):
	extensionList = filename.split(".")
	ofile = open("post_G." + extensionList[1], "wb") # open in write bytes mode
	while 1:
		# receive response from server
		data, addr = sock.recv()
		if data == "ERROR: FILE NOT FOUND":
			ofile.close()
			os.remove(filename)
			print data
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
	"""Main method to start FTA server."""
	# arguments should be port, rwnd
	if len(argv) != 2:
		print "Wrong number of arguments.\npython ftaserver.py $PORT $RWND"
		sys.exit(1)

	port = int(argv[0])
	rwnd = int(argv[1])
	host = '127.0.0.1'

	# create socket and bind to port
	try:
		sock = RTPSocket()
		sock.rwnd = rwnd
		sock.bind((host, port))
		sock.accept()
		# wait for response from client
		while 1:
			data,addr = sock.recv()
			if data:
				dest_host = addr[0]
				dest_port = addr[1]

				#determine which command we are doing and whith what filename
				dataList = data.split(":")
				command = dataList[0]
				if command == "GET":
					filename = dataList[1]
					# send the file (or error msg) to client
					get(filename, sock, dest_host, dest_port, rwnd)	
				elif command == "GET-POST":
					file1 = dataList[1]
					file2 = dataList[2]
					# send the file (or error msg) to client
					get_post(file1, file2, sock, dest_host, dest_port, rwnd)
				else:
					error_msg = "ERROR: COMMAND NOT RECOGNIZED"
					sock.send(error_msg, (host, port))
			else:
				continue
	except Exception, e:
		print "Error"
		print e
		raise # for debugging
 

if __name__ == "__main__":
    main(sys.argv[1:])