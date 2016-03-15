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
		self.socket_host = None
		self.socket_port = None
		self.N = 10
		
	#bind the socket passed in with the desired host and
	def bind(self, source_address):
		self.socket_host = source_address[0]
		self.socket_port = source_address[1]
		self.rtpsocket.bind(source_address)
		
	#connect to the desired host and port
	def connect(self, destination_address):
		#client side 3 way handshake
		self.dsthost = destination_address[0]
		self.dstport = destination_address[1]

		client_isn = random.randint(0,1000)
		srcport = self.socket_port; # Is this right?
		
		header = RTPHeader(srcport, self.dstport, client_isn, 0, 0, 1, 0, 0, 0)
		packet = RTPPacket(header, "")
	
		#send packet with SYN=1 and seq=client_isn
		print "Sending SYN Packet"
		self.send(packet.makeBytes(), destination_address)

		#wait to recieve an ACK from the server
		while 1:
			data,addr = self.recv()
			if data:
				print "Recieved SYNACK"
				header = self.getPacket(data).header
				if header.acknum == (client_isn + 1) and header.ACK == 1 and header.SYN == 1:
					break

		server_isn = header.seqnum
		acknum = server_isn + 1
		srcport = header.dest_port

		header = RTPHeader(srcport, self.dstport, client_isn + 1,  acknum, 1, 0, 0, 0, 0)
		packet = RTPPacket(header, "")

		print "Sending ACK"
		self.send(packet.makeBytes(), destination_address)

		self.socket_port = srcport

	#server side of 3 way handshake
	def accept(self):
		while 1:
			data, dstaddr = self.recv()
			if data:
				print "Received SYN Packet"
				header = self.getPacket(data).header
				if header.SYN == 1:
					break

		client_isn = header.seqnum

		self.dstport = dstaddr[1]
		#generate a random server init number
		server_isn = random.randint(0,1000)
		acknum = client_isn + 1
		srcport = header.dest_port

		header = RTPHeader(srcport, self.dstport, server_isn, acknum, 1, 1, 0, 0, 0)
		packet = RTPPacket(header, "")
	
		#send packet with SYN=1 and seq=client_isn
		print "Sent SYNACK"
		#use seperate functions here
		self.send(packet.makeBytes(), dstaddr)

		#wait to recieve a response from the client
		while 1:
			data, dstaddr = self.recv()
			if data:
				print "Received ACK"
				header = self.getPacket(data).header
				if header.seqnum == (client_isn + 1) and header.acknum == (server_isn + 1) and header.ACK == 1 and header.SYN == 0:
					break

		print "Finished Accept"

	#send data through a socket to an addr
	def send(self, data, addr):
		#list to store the data pieces
		dataSegments = []

		#break up the data into size MSS 
		for segment in range(0, len(data), RTPPacket.MSS):
			if segment+RTPPacket.MSS > len(data): 							#if we go out of bounds:
				dataSegments.append(data[segment:]) 						#	append from segment to the end
			else:
				dataSegments.append(data[segment:segment+RTPPacket.MSS]) 	#	append segment

		packetList = []

		seqnum = 0 #initialize to 0

		for d in dataSegments:
			#create a packet
			source_port = self.socket_port
			dest_port = addr[1] #addr = (host,port)
			acknum = 0
			ACK = 0
			SYN = 0 
			FIN = 0 
			rwnd = 0 
			checksum = 0 
			header = RTPHeader(source_port, dest_port, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum)
			packet = RTPPacket(header, d)
			packetList.append(packet.makeBytes())
			seqnum = seqnum + 1

		#now we have to send the packet list (only send N)
		base = 0 
		nextseqnum = 0
		#timer
		while len(packetList) != 0:
			if(nextseqnum < base + self.N):
				self.rtpsocket.sendto(packetList.pop(nextseqnum), addr)
				if(base == nextseqnum):
					start_timer
				nextseqnum = nextseqnum + 1
			#else: refuse data
			#timeout

			if timer runs out:
				#start_timer
				for i in range(base, nextseqnum - 1):
					self.rtpsocket.sendto(packetList.pop(i))

			#check for response ACKS
			response, dstaddr = self.recv()

			if response: ## and its not corrupt
				responseHeader = self.getPacket(response).header
				base = responseHeader.acknum + 1
				if(base == nextseqnum):
					#stop timer
				else:
					#start_timer

			# for i in range(base, self.N):#send packets base to N
			# 	if i == base:
			# 		#start timer for first unACKED packt
			# 	self.rtpsocket.sendto(packetList[i].makeBytes(), addr)

			# 	response, dstaddr = self.recv()
			# 	if response:
			# 		print "Received response"
			# 		responseHeader = self.getPacket(response).header
			# 		print responseHeader
					#incerement the base
					#mark packets as ACKED


				#if we recieve any during that time where acknum in range (base, base + N)
					#remove all packets from packetList where seqnum before ack number --> cumulative ACK
			#increment base

		#self.rtpsocket.sendto(data, addr)

	# send a SYN
	def sendSYN(self):
		# make SYN packet
		header = RTPHeader(self.socket_port, self.dstport, 0, 0, 0, 1, 0, 0, 0)
		packet = RTPPacket(header, "")
	
		#send packet with SYN=1 and seq=0 (change this)
		print "Sending SYN Packet"
		self.send(packet.makeBytes(), (self.dstport, self.dsthost))

	# send an ACK
	def sendACK(self):
		# make SYN packet
		header = RTPHeader(self.socket_port, self.dstport, 0, 0, 1, 0, 0, 0, 0) # CHANGE THIS not the right seqnum, acknum etc
		packet = RTPPacket(header, "")
	
		#send packet with FIN=1 and seq=0 (change this)
		print "Sending ACK"
		self.send(packet.makeBytes(), (self.dstport, self.dsthost))

	# send a SYNACK
	def sendSYNACK(self):
		pass

	# send a FIN
	def sendFIN(self):
		# make SYN packet
		header = RTPHeader(self.socket_port, self.dstport, 0, 0, 0, 0, 1, 0, 0)
		packet = RTPPacket(header, "")
	
		#send packet with FIN=1 and seq=0 (change this)
		print "Sending FIN Packet"
		self.send(packet.makeBytes(), (self.dstport, self.dsthost))

	#receive data at a socket
	def recv(self):
		#returns data,addr
		# TODO implement unpacking of byte string when packet is received
		return self.rtpsocket.recvfrom(1000)

	# close the socket
	# this will be like how TCP does it
	def close(self):
		# send FIN to server
		self.sendFIN()
		print "Sent FIN Packet"
		
		# wait for ACK from server
		self.setTimeout()
		while 1:
			try:
				data, addr = self.recv()
				if data:
					if self.getPacket(data).isACK:
						print "Received ACK"
						break

			except error: #socket.error
				print "Did not receive FIN packet - socket timed out." # keep waiting I guess? for now

		# wait for server to close (wait for FIN)
		self.setTimeout()
		while 1:
			try:
				data, addr = self.recv()
				if data:
					if self.getPacket(data).isFIN:
						print "Received FIN"
						break
			except error:
				print "Did not receive ACK - socket timed out."

		# send another ACK to the server... -____-
		self.sendACK()
		print "Received FIN from server, sent ACK"

		# wait a while to make sure the ACK gets received
		time.sleep(5) # placeholder

		# finally close the connection
		print "Closing Connection"
		self.rtpsocket.close()

	# takes in the byte string received and parses it
	# returns an RTPPacket
	def getPacket(self, bytes):
		n = struct.unpack("!H", bytes[:2]) # length of data string
		data_size = n[0] # get number from tuple
		unpack_fmt = '!HHHLLBBBHH' + str(data_size) + 's' # header format + s * data_size
		tup = struct.unpack(unpack_fmt, bytes) # unpacks the packet into a tuple

		# now make new RTPPacket object with info from the tuple
		header = RTPHeader(tup[1], tup[2], tup[3], tup[4], tup[5], tup[6], tup[7], tup[8], tup[9])
		packet = RTPPacket(header, tup[10])
		return packet

	def printSocket(self):
		return "Socket at Port: " + str(self.socket_port)

	def setTimeout(self, time):
		self.rtpsocket.settimeout(2)


class RTPPacket:

	MSS = 5 #5 bytes

	def __init__(self, header, data=""):
		self.header = header
		self.data = data
		self.isACKED = False
		self.isSent = False

	# See: http://docs.python.org/2/library/struct.html
	# packs header into bytes and adds header so the string can be sent
	# len_data will be used when client/server receives a packet so it knows the length of the data
	def makeBytes(self):
		len_data = len(self.data)
		packed_header = self.header.makeHeader(len_data)
		return packed_header + self.data # bytes + string

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
		return struct.pack('!HHHLLBBBHH', len_data, self.source_port, self.dest_port, self.seqnum, self.acknum, self.ACK, self.SYN, self.FIN, self.rwnd, self.checksum)
