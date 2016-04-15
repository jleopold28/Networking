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
			if data == "CLOSE CONNECTION":
				sock.serverClose(conn)
				print "CLOSEING SESSION FOR " + str(addr) + "\n"
				break
			#determine which command we are doing and whith what filename
			dataList = data.split(":")
			command = dataList[0]
			if command == "GET":
				filename = dataList[1]
				get(filename, addr)
			elif command == "GET-POST":
				file1 = dataList[1]
				file2 = dataList[2]
				get_post(conn, addr, file1, file2)
			else:
				error_msg = "INVALID COMMAND"
				sock.send(error_msg, addr)
	return

def get_post(conn, addr, file1, file2):
	"""Downloads file1 from cient and uploads file2 to client in same RTP connection."""

	upload_thread = threading.Thread(target = uploadFile, args = (file1, addr))
	download_thread = threading.Thread(target = downloadFile, args = (conn, file2))

	upload_thread.start()
	download_thread.start()

	upload_thread.join()
	download_thread.join() #dont contiunue until both finishe


def get(filename, addr):
	get_thread = threading.Thread(target = uploadFile, args = (filename, addr))
	get_thread.start()
	get_thread.join()

def uploadFile(filename, addr):
	#print "UPLOADING FILE"
	"""Uploads file to client. Called whenever filename is received from server."""
	# check if file exists
	files = [f for f in os.listdir(".") if os.path.isfile(f)]

	if filename not in files:
		error_msg = "ERROR: FILE NOT FOUND"
		sock.send(error_msg, addr)
		return
	else:
		send_file = open(filename, "rb") #rb to read in binary mode

	try:
		msg = send_file.read() # read a the entire file
		sock.send(msg, addr)
		send_file.close()      # close the file

		sock.send("EOF", addr)
		
		print "Sent file to client "

	except Exception, e:
		if send_file:
			send_file.close() # make sure file is closed
		print "Error: Unable to send file."
		print e
		raise

	return

def downloadFile(conn, filename):
	extensionList = filename.split(".")
	ofile = open("post_G_" + extensionList[0] +"."+ extensionList[1], "wb") # open in write bytes mode
	while 1:
		# receive response from server
		data = conn.getData()
		if data == "ERROR: FILE NOT FOUND":
			ofile.close()
			os.remove(filename)
			print data
			break
		elif data == "EOF":
			break
		elif data:
			ofile.write(data)				
		else:
			continue

	ofile.close()
	return

def main(argv):
	"""Main method to start FTA server."""
	# arguments should be port, rwnd
	if len(argv) != 2:
		print "Wrong number of arguments.\npython ftaserver.py $PORT $RWND"
		sys.exit(1)

	# parse command line arguments
	try:
		port = int(argv[0])
		rwnd = int(argv[1])
		host = '127.0.0.1'
	except:
		print "Invalid command line argument(s).\npython ftaserver.py $PORT $RWND"
		sys.exit(1)

	# create socket and bind to port
	try:
		global sock
		sock = RTPSocket() #create only 1 socket
		sock.rwnd = rwnd
		sock.bind((host, port))
		while 1:
			#check the SYN QUE in ACCEPT
			conn, addr = sock.accept()
			if (conn, addr) != ( "","" ):
				newthread = threading.Thread(target = clientSession, args = (conn, addr,))
				newthread.start()

		#sock.close()
	except Exception, e:
		print "Error"
		print e
		raise # for debugging
		#sys.exit(1) # uncomment if we want the server to shut down on error
		
 

if __name__ == "__main__":
    main(sys.argv[1:])