#UDP client
import sys
import socket
import time
from rtp import *

#split the first arument by colon
hostPortList = sys.argv[1].split(":")
#extract the host
host = hostPortList[0]
#extract the port
port = int(hostPortList[1])
#extract the query (ID)
query = sys.argv[2]
cols = "" #string to hold the cols requested

for i in range(3, len(sys.argv)): #iterate over the remaining arguments
	#seperate col values with commas, unless it is the last argument
	if i == len(sys.argv) - 1:
		cols = cols + sys.argv[i]
	else:
		cols = cols + sys.argv[i] +','

try:
	#INITIALIZATION
	s = rtp_socket()

	#DATA TRANSFER
	#send our string in format ID:first_name,last_name, etc.
	rtp_send(s, query + ":" + cols, (host,port))
	print "Sending Message to Server"
	tries = 3
	while tries > 0: #try to recieve response 3 times
		try:
			print "Waiting for a response..."
			s.settimeout(2.0) # wait 2 seconds
			#receive the data from the server
			data, addr = rtp_recv(s)
			if data:
				# if we get a response, stop the loop
				break
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
	rtp_close(s)
	
except:
	#if there is an error, print error message
	data = "Error - Server may be offline"

print data