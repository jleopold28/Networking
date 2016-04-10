"""Client side of File Transfer Applciation with interactive command window."""
import os
import sys
import threading
import Queue

sys.path.insert(0,'..')
from rtp import *

q = Queue.Queue()

def test(host,port):
	conn = sock.connect((host, port))
	q.put(conn)

def connect(sock, host, port, rwnd):
	"""Creates a reliable connection with the FTA server and returns an RTPSocket."""
	try:
		conn = RTPConnection(rwnd, 0)
		conn.connect(sock, (host, port))
		print conn
		#global sock
		#sock = RTPSocket()
		#sock.rwnd = rwnd
		#sock.connect((host,port))
		print "Connected"
		return conn
	except:
		print('Error: Unable to connect to server.')
		raise
		sys.exit(1)
		

def get_post(sock, conn, file1, file2, host, port):
	"""Downloads file1 from server and uploads file2 to server through same RTP connection."""
	command = "GET-POST"
	sock.send(command + ":" + file1 + ":" + file2, (host,port))

	#need to implement threading here
	download_thread = threading.Thread(target = downloadFile, args = (file1, host, port))
	upload_thread = threading.Thread(target = uploadFile, args = (file2, host, port))
	
	download_thread.start()
	upload_thread.start()

	#with lock:
	#	download_thread.join()
	#	upload_thread.join()

	#downloadFile(file1, sock, host, port, rwnd)
	#uploadFile(file2, sock, host, port, rwnd)

def get(sock, conn, filename, host, port):
	"""Downloads file from server."""
	# send filename to server

	#sock.send("GET:" + filename, addr)
	sock.send("GET:" + filename, (host,port))
	#sock.send(command + ":" + filename, (dsthost, dstport)) #tell the server what operation we are doing
	downloadFile(conn, filename)
	#I dont think we need to use threading here, but lets leave it becuase it works for now
	#having the method in a thread cant hurt
	#get_thread = threading.Thread(target = downloadFile, args = (filename, sock, host, port, rwnd))
	#get_thread.start()
	#get_thread.join()

def downloadFile(conn, filename):
	print "DOWNLOADING FILE"
	extensionList = filename.split(".")
	ofile = open("get_F." + extensionList[1], "wb") # open in write bytes mode

	while 1:
		# receive response from server
		data = conn.getData()
		#data, addr = sock.recv(conn_id)
		#data, addr = conn.recv()
		#data = sock.getData()
		if data == "ERROR: FILE NOT FOUND":
			ofile.close()
			os.remove(filename)
			print data
			break
		elif data[-3:]  == "EOF":
			ofile.write(data)	
			break	
		else:
			continue
	ofile.close()

def uploadFile(filename, host, port):
	"""Uploads file to server."""
	# check if file exists
	files = [f for f in os.listdir(".") if os.path.isfile(f)]
	print files
	#print sock.rwnd
	if filename not in files:
		error_msg = "ERROR: FILE NOT FOUND"
		sock.send(error_msg, (host, port))
		send_file = None
	else:
		send_file = open(filename, "rb") #rb to read in binary mode
	print "UPLOADING FILE"
	try:
		# send file to client
		msg = send_file.read(sock.rwnd) # read a portion of the file
		while msg:
			sock.send(msg, (host, port))
			msg = send_file.read(sock.rwnd)
		send_file.close() # close the file
		sock.send("FILE FINISHED SENDING", (host, port))
		print "sent file to client"
	except Exception, e:
		if send_file:
			send_file.close() # make sure file is closed
		print "Error: Unable to send file."
		print e
		#lock.release()

def main(argv):
	"""Main method for FTA client interactive command window."""
	# arguments should be H:P W
	if len(argv) != 2:
		print "Wrong number of arguments.\npython ftaclient.py $HOST:$PORT $RWND"
		sys.exit(1)


	arg0 = argv[0].split(":")
	host = arg0[0]
	port = int(arg0[1])
	rwnd = int(argv[1])

	disconnect = False

	sock = RTPSocket()
	sock.rwnd = rwnd

	#connectThread = threading.Thread(target = test, args = (host,port,))

	#with lock:
	#	connectThread.start()
	#	conn = q.get()

	conn = sock.connect((host,port))

	while disconnect == False:
		command = raw_input("> ")
		if command == "disconnect":
			disconnect = True
			# disconnect from the server gracefully
			# todo send FIN to server
			try:
				#sock.clientClose()
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
				get_post(conn, f, g, host, port)
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
				get(sock, conn, f, host, port)
			except:
				print "Error downloading file."
				raise # for debugging
		else:
			print "Invalid command."

	sys.exit(1)
  

if __name__ == "__main__":
    main(sys.argv[1:])

