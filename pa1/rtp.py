#RTP Functions
import socket
import sys

#create a new RTP socket of UDP type
def rtp_socket():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	print "Socket Created"
	return s

#bind the socket passed in with the desired host and port
def rtp_bind(s, host, port):
	s.bind((host, port))
	print "Socket Bind Complete"

#listen on the socket for data - not sure if we need this function....
def rtp_listen(s):
	s.listen(1);
	print "Listening on Socket..."

#connect to the desired host and port
def rtp_connect(s, host,port):
	#connect to the server
	s.connect((host,port))

#send data through a socket to an addr
def rtp_send(s, data, addr):
	s.sendto(data, addr)

#receive data at a socket
def rtp_recv(s):
	return s.recvfrom(1024)

#close the socket passed in
def rtp_close(s):
	print "Closing Connection"
	s.close()