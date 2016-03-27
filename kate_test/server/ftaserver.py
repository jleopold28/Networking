"""Server side of File Transfer Application."""
import os
import sys
import time
import threading
sys.path.insert(0,'..')
from rtp import *

lock = threading.Lock()
sock = None

def clientSession(conn, sock):
	print conn
	#print connections[cid]
	while 1:
		data,addr = conn.recv(sock)
		#ata = sock.getData()
		if data:
			#dest_host = addr[0]
			#dest_port = addr[1]
			#determine which command we are doing and whith what filename
			dataList = data.split(":")
			command = dataList[0]
			if command == "GET":
				filename = dataList[1]
				# send the file (or error msg) to client
				get(sock, conn, filename)	
			elif command == "GET-POST":
				file1 = dataList[1]
				file2 = dataList[2]
				# send the file (or error msg) to client
				get_post(sock, conn, file1, file2)
			else:
				error_msg = "ERROR: COMMAND NOT RECOGNIZED"
				conn.send(sock, error_msg, (conn.dst_host, conn.dst_port))
				#sock.send(error_msg, (dest_host, dest_port))
		else:
			continue

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

def get(sock, conn, filename):
	#upload_thread = threading.Thread(target = uploadFile, args = (filename, sock, host, port, rwnd))
	#upload_thread.start()
	#upload_thread.join()
	uploadFile(sock, conn, filename)

def uploadFile(sock, conn, filename):
	print "UPLOADING FILE"
	host = conn.dst_host
	port = conn.dst_port
	"""Uploads file to client. Called whenever filename is received from server."""
	# check if file exists
	files = [f for f in os.listdir(".") if os.path.isfile(f)]
	print files
	#print sock.rwnd
	if filename not in files:
		error_msg = "ERROR: FILE NOT FOUND"
		conn.send(sock, error_msg, (host,port))
		#sock.send(error_msg, (host, port))
		send_file = None
	else:
		send_file = open(filename, "rb") #rb to read in binary mode
	try:
		# send file to client
		msg = send_file.read(conn.rwnd) # read a portion of the file
		while msg:
			conn.send(sock, msg, (host,port))
			#sock.send(msg, (host, port))
			msg = send_file.read(conn.rwnd)
		send_file.close() # close the file
		conn.send(sock, "FILE FINISHED SENDING", (host, port))
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
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#bind it to the server host and port
		sock.bind((host, port))

		#sock = RTPSocket()
		#sock.rwnd = rwnd
		#sock.bind((host, port))

		#mainThread = threading.Thread()
		#mainThread.setDaemon(True)

		#threads = []
		#connections = []
		#connectionID
		cid = 0
		while 1:
			print "Waiting for incoming connections..."
			conn = RTPConnection(rwnd, cid)
			conn.accept(sock, (host, port))
			#connections.append(conn)
			newthread = threading.Thread(target = clientSession, args = (conn,sock))
			#newthread = threading.Thread(target = sock.accept(), args = (client_addr, ))
			newthread.start()
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