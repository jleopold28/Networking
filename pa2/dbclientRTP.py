#RDT client for RDBA
import sys
import time
import random
sys.path.insert(0,'..')
from rtp import *

sock = None

def main(argv):
	#split the first arument by colon
	hostPortList = argv[1].split(":")
	#extract the server_host
	server_host = hostPortList[0]
	#extract the server_port
	server_port = int(hostPortList[1])
	#extract the query (ID)
	query = argv[2]
	cols = "" #string to hold the cols requested

	for i in range(3, len(sys.argv)): #iterate over the remaining arguments
		#seperate col values with commas, unless it is the last argument
		if i == len(sys.argv) - 1:
			cols = cols + sys.argv[i]
		else:
			cols = cols + sys.argv[i] +','

	try:
		#INITIALIZATION
		global sock
		sock = RTPSocket()
		sock.rwnd = 512

		conn_id = sock.connect((server_host, server_port))
		
		#DATA TRANSFER
		sock.send(query + ":" + cols, (server_host, server_port))

		print "Sending Message to Server"
		tries = 3
		while tries > 0: #try to recieve response 3 times
			try:
				print "Waiting for a response..."
				#receive the data from the server
				data = sock.getData(conn_id)
				if data:
					print "Received response from server"
					# if we get a response, stop the loop
					break
				time.sleep(2)
			except:
				# if there is a timeout or the server is offline
				print "The server has not answered in the last two seconds"
				print "retrying..."
				if tries == 1:
					#if we are on the last try and there was no response, we set the error message
					data = "There was no response from the server"
			tries = tries - 1

		#TERMINATION
		print data
		#close the socket
		sock.send("CLOSE CONNECTION", (server_host, server_port))
		sock.clientClose(conn_id)
		
	except Exception, e:
		#if there is an error, print error message
		print e
		data = "Error - Server may be offline"

if __name__ == "__main__":
    main(sys.argv)