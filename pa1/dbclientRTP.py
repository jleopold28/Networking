#RDT client for RDBA
import sys
import time
import random
from rtp import *

#split the first arument by colon
hostPortList = sys.argv[1].split(":")
#extract the server_host
server_host = hostPortList[0]
#extract the server_port
server_port = int(hostPortList[1])
#extract the query (ID)
query = sys.argv[2]
cols = "" #string to hold the cols requested

for i in range(3, len(sys.argv)): #iterate over the remaining arguments
	#seperate col values with commas, unless it is the last argument
	if i == len(sys.argv) - 1:
		cols = cols + sys.argv[i]
	else:
		cols = cols + sys.argv[i] +','


#s = RTPSocket()
#s.connect((server_host, server_port))
#print s.printSocket()
#s.close() 

try:
	#INITIALIZATION
	s = RTPSocket()
	s.connect((server_host, server_port))
	print s.printSocket()
	time.sleep(2)
	
	#DATA TRANSFER
	#send our string in format ID:first_name,last_name, etc.
	source_port = s.socket_port
	seqnum = random.randint(0,1000)
	acknum = random.randint(0,1000)
	header = RTPHeader(source_port, server_port, seqnum, acknum, 0, 0, 0, 0, 0)
	packet = RTPPacket(header, query + ":" + cols)

	s.send(packet.makeBytes(), (server_host, server_port))

	print "Sending Message to Server"
	tries = 3
	while tries > 0: #try to recieve response 3 times
		try:
			print "Waiting for a response..."
			#receive the data from the server
			data, addr = s.recv()
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
	#close the socket
	s.close()
except:
	#if there is an error, print error message
	data = "Error - Server may be offline"

packet = s.getPacket(data)
print packet.data