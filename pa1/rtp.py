#RTP Functions
from inspect import getmembers
import pprint
import random
import socket
import struct # for making packet headers into byte string


class RTPSocket:

	#construct a new RTPSocket
	def __init__(self):
		self.rtpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		
	#bind the socket passed in with the desired host and
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
		srcport = 0; #??
		
		header = RTPHeader(srcport, dstport, client_isn, 0, 0, 1, 0, 0, 0)
		packet = RTPPacket(header, "")
	
		#send packet with SYN=1 and seq=client_isn
		self.send(packet.makeBytes()), destination_address)


		#wait to recieve an ACK from the server
		while 1:
			data,addr = self.recv()
			if data:
				dataList = data.split(",")
				server_acknum = dataList[3]
				server_ack = dataList[4]
				server_syn = dataList[5]
				print dataList
				#only continue is the acknum = client_isn+1 and the syn and ack bit = 1
				if server_acknum == str(client_isn + 1) and server_ack == "1" and server_syn == "1":
					break


		server_isn = int(dataList[1])
		acknum = server_isn + 1

		print "Sending ACK"
		#send packet with SYN=0 and seq = clientisn + 1
		#acknum is the server_isn + 1

		header = RTPHeader(srcport, dstport, client_isn + 1,  acknum, 1, 0, 0, 0, 0, 0)
		packet = RTPPacket(header, "")

		#packet2 = self.packet("", dstport, client_isn + 1, acknum, 1, 0, 0)
		self.send(packet.makeBytes(), destination_address)

	#server side of 3 way handshake
	def accept(self):
		#wait for syn bit to be recieved
		while 1:
			data, dstaddr = self.recv()
			print data
			if data:
				dataList = data.split(",")
				#extract the syn bit
				syn = dataList[5]
				if syn == "1":
					break

		print "Connection Granted"
		#extract the client_isn for incrementing
		client_isn = int(dataList[2])
		dstport = dstaddr[1]
		#generate a random server init number
		server_isn = random.randint(0,1000);
		acknum = client_isn + 1

		#send ACK packet with:
		#SACK = 1, SYN = 1
		#seq=server_isn , acknum=client_isn+1
		header = RTPHeader(srcport, dstport, client_isn, 0, 0, 1, 0, 0, 0, 0, 0)
		packet = RTPPacket(header, "")
	
		#send packet with SYN=1 and seq=client_isn
		self.send(packet.makeBytes(), destination_address)

		packet = self.packet("", dstport, server_isn, acknum, 1, 1, 0, 0, 0)
		self.send(packet.makeBytes(), dstaddr)

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
		# TODO implement unpacking of byte string when packet is received
		return self.rtpsocket.recvfrom(1000)

	#close the socket passed in
	def close(self):
		print "Closing Connection"
		self.rtpsocket.close()

	#make a packet with the rtp header
	# do we need this now that we have the RTPPacket class?
	def packet(self, data, dstport, seqnum, acknum, ACK = 0, SYN = 0, FIN = 0):
		header = str(dstport) + "," + str(seqnum) + "," + str(acknum) + "," + str(ACK) + "," + str(SYN) + "," + str(FIN)
		packet = header + ":" + data
		return packet

class RTPPacket:

	def __init__(self, header, data=""):
		self.header = header
		self.data = data

	
	# takes packet and unpacks into header and data
	# returns a list [header, data] where header is a tuple and data is a string
	def unpack(self):
		pass 
		# todo unpack header
		n = struct.unpack("!H", )
		# todo get data
		# todo return [header, data]

	# See: http://docs.python.org/2/library/struct.html
	# packs header into bytes and adds header so the string can be sent
	# len_data will be used when client/server receives a packet so it knows the length of the data
	def makeBytes(self):
		len_data = len(data)
		packed_header = header.makeHeader(len_data)
		return packed_header + data # bytes + string

	# are these methods even useful? IDK but here they are
	# return True if ACK
	def isACK(self):
		return self.header.ACK == 1

	# return True if SYN
	def isSYN(self):
		return self.header.SYN == 1

	# return True if FIN
	def isFIN(self):
		return self.header.FIN == 1


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

	# packs header into bytes
	# added new len_data argument so we know the length of the data when we unpack
	def makeHeader(self, len_data = 0):
		return struct.pack('!HHHLLBBBHHH', len_data, self.source_port, self.dest_port, self.seqnum, self.acknum, self.ACK, self.SYN, self.FIN, self.rwnd, self.checksum)
