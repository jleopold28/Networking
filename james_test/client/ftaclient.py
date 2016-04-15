"""Client side of File Transfer Applciation with interactive command window."""
import os
import sys
import threading
import Queue

sys.path.insert(0,'..')
from rtp import *

sock = None

def get_post(conn, file1, file2, addr):
	"""Downloads file1 from server and uploads file2 to server through same RTP connection."""
	command = "GET-POST"
	sock.send(command + ":" + file1 + ":" + file2, addr)

	download_thread = threading.Thread(target = downloadFile, args = (conn, file1))
	upload_thread = threading.Thread(target = uploadFile, args = (file2, addr))
	
	download_thread.start()
	upload_thread.start()


def get(conn, filename, addr):
	"""Downloads file from server."""
	sock.send("GET:" + filename, addr) #tell the server what operation we are doing
	downloadFile(conn,filename)
	

def downloadFile(conn, filename):
	#print "DOWNLOADING FILE"
	fileList = filename.split(".")
	ofile = open("get_F_" + fileList[0] + "." +fileList[1], "wb") # open in write bytes mode

	while 1:
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
	#print "FINSHED DOWNLOADING"
	return

def uploadFile(filename, addr):
	"""Uploads file to server."""
	# check if file exists
	files = [f for f in os.listdir(".") if os.path.isfile(f)]

	if filename not in files:
		error_msg = "ERROR: FILE NOT FOUND"
		sock.send(error_msg, addr)
		return
	else:
		send_file = open(filename, "rb") #rb to read in binary mode

	#print "UPLOADING FILE"
	try:
		msg = send_file.read() 
		sock.send(msg, addr)
		send_file.close()
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


	arg0 = argv[0].split(":")
	host = arg0[0]
	port = int(arg0[1])
	rwnd = int(argv[1])

	disconnect = False

	global sock
	sock = RTPSocket()
	sock.rwnd = rwnd

	conn = sock.connect((host,port))

	while disconnect == False:
		command = raw_input("> ")
		if command == "disconnect":
			sock.send("CLOSE CONNECTION", (host, port)) 
			sock.clientClose(conn)
			print "\n\n"
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
			g = cmd_list[2]
			try:
				get_post(conn, f, g, (host, port))
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
				get(conn, f, (host,port))
			except:
				print "Error downloading file."
				raise # for debugging
		else:
			print "Invalid command."

	sys.exit(1)
  

if __name__ == "__main__":
    main(sys.argv[1:])

