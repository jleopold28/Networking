#RTP Functions
import socket
import random
from inspect import getmembers
import pprint

class RTPSocket:

	#construct a new RTPSocket
	def __init__(self):
		self.rtpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		
	#bind the socket passed in with the desired host and port
	def bind(self, source_address):
		self.source_port = source_address[1]
		self.rtpsocket.bind(source_address)
		

	#connect to the desired host and port
	def connect(self, destination_address):
		print "Connection Request"
		#client side 3 way handshake
		dsthost = destination_address[0]
		dstport = destination_address[1]

		client_isn = random.randint(0,1000);

		#send packet with SYN=1 and seq=client_isn
		#packet = self.packet("", dstport, client_isn, 0, 0, 1, 0)
		
		srcport = 0; #??
		
		header = RTPHeader(srcport, dstport, client_isn, 0, 0, 1, 0, 0, 0)
		packet = RTPPacket(header, "")

		self.send(packet.getString(), destination_address)

		#wait to recieve an ACK from the server
		while 1:
			data,addr = self.recv()
			if data:
				dataList = data.split(",")
				server_acknum = dataList[2]
				server_ack = dataList[3]
				server_syn = dataList[4]
				print dataList
				#only continue is the acknum = client_isn+1 and the syn and ack bit = 1
				if server_acknum == str(client_isn + 1) and server_ack == "1" and server_syn == "1":
					break


		server_isn = int(dataList[1])
		acknum = server_isn + 1

		print "Sending ACK"
		#send packet with SYN=0 and seq = clientisn + 1
		#acknum is the server_isn + 1
		packet2 = self.packet("", dstport, client_isn + 1, acknum, 1, 0, 0)
		self.send(packet2, dstaddr)

	#server side of 3 way handshake
	def accept(self):
		#wait for syn bit to be recieved
		while 1:
			data, dstaddr = self.recv()
			if data:
				dataList = data.split(",")
				#extract the syn bit
				syn = dataList[4]
				if syn == "1":
					break

		print "Connection Granted"
		#extract the client_isn for incrementing
		client_isn = int(dataList[1])
		dstport = dstaddr[1]
		#generate a random server init number
		server_isn = random.randint(0,1000);
		acknum = client_isn + 1

		#send ACK packet with:
		#SACK = 1, SYN = 1
		#seq=server_isn , acknum=client_isn+1
		packet = self.packet("", dstport, server_isn, acknum, 1, 1, 0)
		self.send(packet, dstaddr)

		#wait to recieve a response from the client
		##### MAY NEED TO TAKE THIS PART OUT
		# while 1:
		# 	data, dstaddr = s.recvfrom(1000)
		# 	if data:
		# 		dataList = data.split(",")
		# 		seqnum = dataList[1] # client_isn + 1
		# 		acknum = dataList[2] # server_isn + 1
		# 		ack = dataList[3] # 1
		# 		syn = dataList[4] # 0
		# 		#client should send us packet with the above values
		# 		if seqnum == str(client_isn + 1) and acknum == str(server_isn + 1) and ack == "1" and syn == "0":
		# 			break
		# print "Finished Accept"

	#send data through a socket to an addr
	def send(self, data, addr):
		self.rtpsocket.sendto(data, addr)

	#receive data at a socket
	def recv(self):
		#returns data,addr
		return self.rtpsocket.recvfrom(1000)

	#close the socket passed in
	def close(self):
		print "Closing Connection"
		self.rtpsocket.close()

	#make a packet with the rtp header
	def packet(self, data, dstport, seqnum, acknum, ACK = 0, SYN = 0, FIN = 0):
		header = str(dstport) + "," + str(seqnum) + "," + str(acknum) + "," + str(ACK) + "," + str(SYN) + "," + str(FIN)
		packet = header + ":" + data
		return packet

class RTPPacket:

	def __init__(self, header, data=""):
		self.header = header
		self.data = data

	def getString(self):
		return self.header.getString() + ":" + self.data


class RTPHeader:

	def __init__(self, source_port, dest_port, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum):
		self.source_port = source_port
		self.dest_port = dest_port
		self.seqnum = seqnum
		self.acknum = acknum
		self.ACK = ACK
		self.SYN = SYN
		self.FIN = FIN
		self.rwnd = rwnd
		self.checksum = checksum

	def getString(self):
		return str(self.source_port) + "," + str(self.dest_port) + "," + str(self.seqnum) + "," + str(self.acknum) + "," + str(self.ACK) + "," + str(self.SYN) + "," + str(self.FIN) + "," + str(self.rwnd) +"," + str(self.checksum)

