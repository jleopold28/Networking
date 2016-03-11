#RTP Functions
import socket
import random

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
def rtp_connect(s, dsthost, dstport):
	#client side 3 way handshake
	dstaddr = (dsthost, dstport)
	client_isn = random.randint(0,1000);

	#send packet with SYN=1 and seq=client_isn
	packet = rtp_packet("", dstport, client_isn, 0, 0, 1, 0)
	rtp_send(s, packet, dstaddr)

	#wait to recieve an ACK from the server
	while 1:
		data,addr = rtp_recv(s)
		if data:
			dataList = data.split(":")
			server_acknum = dataList[2]
			server_ack = dataList[3]
			server_syn = dataList[4]
			#only continue is the acknum = client_isn+1 and the syn and ack bit = 1
			if server_acknum == str(client_isn + 1) and server_ack == "1" and server_syn == "1":
				break


	server_isn = int(dataList[1])
	acknum = server_isn + 1

	#send packet with SYN=0 and seq = clientisn + 1
	#acknum is the server_isn + 1
	packet2 = rtp_packet("", dstport, client_isn + 1, acknum, 1, 0, 0)
	rtp_send(s, packet2, dstaddr)

#returns a connection socket and addr
#conn,addr = s.accept()

#server side of 3 way handshake
def rtp_accept(s):
	#wait for syn bit to be recieved
	while 1:
		data, dstaddr = rtp_recv(s)
		if data:
			dataList = data.split(":")
			#extract the syn bit
			syn = dataList[4]
			if syn == "1":
				break

	#extract the client_isn for incrementing
	client_isn = int(dataList[1])
	dstport = dstaddr[1]
	#generate a random server init number
	server_isn = random.randint(0,1000);
	acknum = client_isn + 1

	#send ACK packet with:
	#SACK = 1, SYN = 1
	#seq=server_isn , acknum=client_isn+1
	packet = rtp_packet("", dstport, server_isn, acknum, 1, 1, 0)
	rtp_send(s, packet, dstaddr)

	#wait to recieve a response from the client
	##### MAY NEED TO TAKE THIS PART OUT
	while 1:
		data, dstaddr = s.recvfrom(1000)
		if data:
			dataList = data.split(":")
			seqnum = dataList[1] # client_isn + 1
			acknum = dataList[2] # server_isn + 1
			ack = dataList[3] # 1
			syn = dataList[4] # 0
			#client should send us packet with the above values
			if seqnum == str(client_isn + 1) and acknum == str(server_isn + 1) and ack == "1" and syn == "0":
				break

#send data through a socket to an addr
def rtp_send(s, data, addr):
	s.sendto(data, addr)

#receive data at a socket
def rtp_recv(s):
	#returns data,addr
	return s.recvfrom(1000)

#close the socket passed in
def rtp_close(s):
	print "Closing Connection"
	s.close()

#make a packet with the rtp header
def rtp_packet(data, dstport, seqnum, acknum, ACK = 0, SYN = 0, FIN = 0):
	header = str(dstport) + ":" + str(seqnum) + ":" + str(acknum) + ":" + str(ACK) + ":" + str(SYN) + ":" + str(FIN)
	packet = header + ":" + data
	return packet

def rtp_settimeout(s, timeout):
	s.settimeout(timeout)