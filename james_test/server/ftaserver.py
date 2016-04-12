"""Server side of File Transfer Application."""
import os
import sys
import time
import threading
import Queue
sys.path.insert(0,'..')
from rtp import *

sock = None

def clientSession(conn, addr):
	print "STARTING CLIENT SESSION at " + str(addr)

	while 1:
		data = conn.getData()
		if data:
			#determine which command we are doing and whith what filename
			dataList = data.split(":")
			command = dataList[0]
			if command == "GET":
				filename = dataList[1]
				# send the file (or error msg) to client
				get(conn, addr, filename)
			elif command == "GET-POST":
				file1 = dataList[1]
				file2 = dataList[2]
				# send the file (or error msg) to client
				get_post(conn, addr, file1, file2)
				#sock.send(error_msg, (dest_host, dest_port))

def get_post(file1, file2, host, port):
	"""Downloads file1 from cient and uploads file2 to client in same RTP connection."""
	#need to implement threading here

	upload_thread = threading.Thread(target = uploadFile, args = (file1, host, port))
	download_thread = threading.Thread(target = downloadFile, args = (file2, host, port))

	upload_thread.start()
	download_thread.start()

	#with lock:
	#	upload_thread.join()
	#	download_thread.join()
	#download_thread = threading.Thread(target = downloadFile, args = (file2, sock, host, port, rwnd))
	#download_thread.start()
	#upload_thread.join()

	#uploadFile(file1, sock, host, port, rwnd)
	#downloadFile(file2, sock, host, port, rwnd)
	#pass

def get(conn, addr, filename):
	#upload_thread = threading.Thread(target = uploadFile, args = (filename, sock, host, port, rwnd))
	#upload_thread.start()
	#upload_thread.join()
	uploadFile(conn, addr, filename)

def uploadFile(conn, addr, filename):
	#print "UPLOADING FILE"
	"""Uploads file to client. Called whenever filename is received from server."""
	# check if file exists
	files = [f for f in os.listdir(".") if os.path.isfile(f)]
	#print files
	if filename not in files:
		error_msg = "ERROR: FILE NOT FOUND"
		sock.send(error_msg, addr)
		send_file = None
	else:
		send_file = open(filename, "rb") #rb to read in binary mode

	try:
		# send file to client
		msg = send_file.read() # read a the entire file?
		sock.send(msg, addr)
		send_file.close()      # close the file
		sock.send("EOF", addr)
		print "Sent file to client"
	except Exception, e:
		if send_file:
			send_file.close() # make sure file is closed
		print "Error: Unable to send file."
		print e
		#lock.release()

def downloadFile(filename, host, port):
	extensionList = filename.split(".")
	ofile = open("post_G." + extensionList[1], "wb") # open in write bytes mode
	print "DOWNLOADING FILE"
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
		global sock
		sock = RTPSocket() #create only 1 socket
		sock.rwnd = rwnd
		sock.bind((host, port))
		while 1:
			#check the SYN QUE in ACCEPT
			conn, addr = sock.accept()
			if (conn, addr) != ("",""):
				newthread = threading.Thread(target = clientSession, args = (conn, addr,))
				newthread.start()

		sock.close()
	except Exception, e:
		print "Error"
		print e
		raise # for debugging
		
 

if __name__ == "__main__":
    main(sys.argv[1:])