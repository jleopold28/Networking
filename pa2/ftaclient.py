"""Client side of File Transfer Applciation with interactive command window."""
import os
import sys
import threading
from rtp import *

sock = None
lock = threading.Lock()

def get_post(conn_id, file1, file2, addr):
	"""Downloads file1 from server and uploads file2 to server through same RTP connection."""
	command = "GET-POST"
	
	with lock:
		sock.send(command + ":" + file1 + ":" + file2, addr)

	download_thread = threading.Thread(target = downloadFile, args = (conn_id, file1))
	upload_thread = threading.Thread(target = uploadFile, args = (file2, addr))

	download_thread.start()
	upload_thread.start()

	download_thread.join()
	upload_thread.join()

def get(conn_id, filename, addr):
	"""Downloads file from server."""
	with lock:
		sock.send("GET:" + filename, addr) #tell the server what operation we are doing
	#get_thread = threading.Thread(target = downloadFile, args = (conn, filename))
	#get_thread.start()
	#get_thread.join()
	downloadFile(conn_id,filename)

def downloadFile(conn_id, filename):
	print "DOWNLOADING FILE"
	fileList = filename.split(".")
	ofile = open("get_F." +fileList[1], "wb") # open in write bytes mode

	while 1:
		#data = conn.getData()
		data = sock.getData(conn_id)

		if data == "ERROR: FILE NOT FOUND":
			ofile.close()
			os.remove("get_F." + fileList[1])#os.remove(filename)
			print data
			break
		elif data == "EOF":
			break
		elif data:
			ofile.write(data)
		else:
			continue
	ofile.close()
	print "FINSHED DOWNLOADING\n"
	return

def uploadFile(filename, addr):
	"""Uploads file to server."""
	# check if file exists
	files = [f for f in os.listdir(".") if os.path.isfile(f)]

	if filename not in files:
		error_msg = "ERROR: FILE NOT FOUND"
		with lock:
			sock.send(error_msg, addr)
		return
	else:
		send_file = open(filename, "rb") #rb to read in binary mode

	#print "UPLOADING FILE"
	try:
		msg = send_file.read() 
		with lock:
			sock.send(msg, addr)
		send_file.close()
		with lock:
			sock.send("EOF", addr)
		print "sent file to server"
	except Exception, e:
		if send_file:
			send_file.close() # make sure file is closed
		print "Error: Unable to send file."
		print e
	return
		
def main(argv):
	"""Main method for FTA client interactive command window."""
	# arguments should be H:P W
	if len(argv) != 2:
		print "Wrong number of arguments.\npython ftaclient.py $HOST:$PORT $RWND"
		sys.exit(1)

	# parse command line arguments
	try:
		arg0 = argv[0].split(":")
		host = arg0[0]
		port = int(arg0[1])
		rwnd = int(argv[1])
	except:
		print "Invalid argument(s).\npython ftaclient.py $HOST:$PORT $RWND"
		sys.exit(1)
	
	disconnect = False

	global sock
	sock = RTPSocket()
	sock.rwnd = rwnd

	conn_id = sock.connect((host,port))

	while disconnect == False:
		command = raw_input("> ")
		if command == "disconnect":
			sock.send("CLOSE CONNECTION", (host, port)) 
			sock.clientClose(conn_id)
			print "\n"
			disconnect = True
		elif "get-post" in command:
			# arguments should be F G
			# F: download file F from the server
			# G: upload file G to the server through same RTP connection
			cmd_list = command.split(" ")
			if len(cmd_list) != 3:
				print "Wrong number of arguments for get-post (expected 2)"
				continue
			f = cmd_list[1]
			if "." not in f:
				print "Invalid filename: " + f
				continue
			g = cmd_list[2]
			if "." not in g:
				print "Invalid filename: " + g
				continue
			try:
				get_post(conn_id, f, g, (host, port))
			except Exception,e:
				print e
				print "Error downloading or uploading file."

		elif "get" in command:
			# argument should be F
			# F: download file F from the server
			cmd_list = command.split(" ")
			if len(cmd_list) != 2:
				print "Wrong number of arguments for get (expected 1)"
				continue
			f = cmd_list[1]
			# check if valid filename (filename.extension)
			if "." not in f:
				print "Invalid filename: " + f
				continue
			try:
				get(conn_id, f, (host,port))
			except:
				print "Error downloading file."
				raise # for debugging
		else:
			print "Invalid command."

	sys.exit(1)
  

if __name__ == "__main__":
    main(sys.argv[1:])

