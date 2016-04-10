"""Server side of File Transfer Application."""
import os
import sys
import time
import threading
import Queue
sys.path.insert(0,'..')
from rtp import *

q = Queue.Queue()

def test():
	conn, addr = sock.accept()
	print "AFTER ACCEPT"
	print conn
	print addr
	q.put((conn,addr))

def clientSession(conn, addr):
	print "STARTING CLIENT SESSION at " + str(addr)
	#print connections[cid]
	#listen = threading.Thread(target = sock.listen())
	#listen.start()

	while 1:
		#data = sock.getData(conn_id)
		data = conn.getData()
		if data:
			#dest_host = addr[0]
			#dest_port = addr[1]
			#determine which command we are doing and whith what filename
			dataList = data.split(":")
			command = dataList[0]
			if command == "GET":
				filename = dataList[1]
				# send the file (or error msg) to client
				get(conn, addr, filename)
				break
			elif command == "GET-POST":
				file1 = dataList[1]
				file2 = dataList[2]
				# send the file (or error msg) to client
				get_post(conn, addr, file1, file2)
				break
				#sock.send(error_msg, (dest_host, dest_port))
			#ELSE INVALID COMMAND
			#EDIT THIS
		else:
			continue

	sock.close()

# class clientThread(threading.Thread):
# 	def __init__(self, ip, port):
# 		threading.Thread.__init__(self)
# 		self.ip = ip
# 		self.port = port
# 		#self.sock = sock
# 		print "New thread started for "+ip+":"+str(port)

# 	def run(self):
# 		print "RUNNING THREAD for" + self.ip + ":" + str(self.port)
# 		while 1:
# 			global sock
# 			data,addr = sock.recv()
# 			if data:
# 				dest_host = addr[0]
# 				dest_port = addr[1]

# 				#determine which command we are doing and whith what filename
# 				dataList = data.split(":")
# 				command = dataList[0]
# 				if command == "GET":
# 					filename = dataList[1]
# 					# send the file (or error msg) to client
# 					get(filename, sock, dest_host, dest_port, sock.rwnd)	
# 				elif command == "GET-POST":
# 					file1 = dataList[1]
# 					file2 = dataList[2]
# 					# send the file (or error msg) to client
# 					get_post(file1, file2, sock, dest_host, dest_port, sock.rwnd)
# 				else:
# 					error_msg = "ERROR: COMMAND NOT RECOGNIZED"
# 					sock.send(error_msg, (dest_host, dest_port))
# 			else:
# 				#print "C"
# 				continue

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
	print "UPLOADING FILE"
	#host = sock.connections[conn_id].dst_host
	#port = sock.connections[conn_id].dst_host
	#host = conn.dst_host
	#port = conn.dst_port
	"""Uploads file to client. Called whenever filename is received from server."""
	# check if file exists
	files = [f for f in os.listdir(".") if os.path.isfile(f)]
	print files
	#print sock.rwnd
	if filename not in files:
		error_msg = "ERROR: FILE NOT FOUND"
		sock.send(error_msg, addr)
		#sock.send(error_msg, (host, port))
		send_file = None
	else:
		send_file = open(filename, "rb") #rb to read in binary mode
	try:
		# send file to client
		msg = send_file.read() # read a portion of the file
		#while msg:
		print msg
		sock.send(msg, addr)
		#	msg = send_file.read(conn.rwnd)
		send_file.close() # close the file
		sock.send("EOF", addr)
		print "sent file to client"
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
		#create only 1 UDP socket
		#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#bind it to the server host and port
		#sock.bind((host, port))

		sock = RTPSocket()
		sock.rwnd = rwnd
		sock.bind((host, port))

		#listenThread = threading.Thread(target = listen)
		#listenThread.start()
		#thread.start_new_thread(sock.listen())

		#mainThread = threading.Thread()
		#mainThread.setDaemon(True)

		#threads = []
		#connections = []
		#connectionID
		#conn_id = 0

		#test = threading.Thread(target = makeconnection)
		#test.start()
		while 1:
			#print "Waiting for incoming connections..."
			#acceptThread = threading.Thread(target = test)

			#with lock:
		#		print "we have the lock"
		#		acceptThread.start()
		#		print "after accept"
		#		conn, addr = q.get()
		#		print conn
		#		print addr
		#		print "test"
			conn, addr = sock.accept()
			if (conn, addr) != ("",""):
				newthread = threading.Thread(target = clientSession, args = (conn, addr,))
				newthread.start()
				print "new thread started"

		sock.close()
		#while 1:
		#		print "Waiting for incoming connections..."
			#conn, addr = sock.accept()
		#	test = threading.Thread(target = sock.accept())
	#		test.start()
	#		print test

			#newthread = threading.Thread(target = clientSession)
	#		newthread = threading.Thread(target = clientSession, args = (conn, addr,))
	#		newthread.start()
			#connections.append(conn)

		#conn = RTPConnection(sock, rwnd, cid)
		#conn.accept((host, port))
		#clientSession(conn)
			#connections.append(conn)
			#newthread = threading.Thread(target = clientSession, args = (conn,))
			#newthread = threading.Thread(target = sock.accept(), args = (client_addr, ))
			#newthread.start()
			#clientSession(client_addr)
			#newthread = clientThread(client_addr[0], client_addr[1])
			#newthread.setDaemon(True)
			
			#newthread.start()
			#newthread.join()
			#threads.append(newthread)

		#for t in threads:
		#	t.join()
		
		#sock.accept()

		# wait for response from client
		# while 1:
		# 	data,addr = sock.recv()
		# 	if data:
		# 		dest_host = addr[0]
		# 		dest_port = addr[1]

		# 		#determine which command we are doing and whith what filename
		# 		dataList = data.split(":")
		# 		command = dataList[0]
		# 		if command == "GET":
		# 			filename = dataList[1]
		# 			# send the file (or error msg) to client
		# 			get(filename, sock, dest_host, dest_port, rwnd)	
		# 		elif command == "GET-POST":
		# 			file1 = dataList[1]
		# 			file2 = dataList[2]
		# 			# send the file (or error msg) to client
		# 			get_post(file1, file2, sock, dest_host, dest_port, rwnd)
		# 		else:
		# 			error_msg = "ERROR: COMMAND NOT RECOGNIZED"
		# 			sock.send(error_msg, (host, port))
		# 	else:
		# 		continue
	except Exception, e:
		print "Error"
		print e
		raise # for debugging
		
 

if __name__ == "__main__":
    main(sys.argv[1:])