#RTP Functions
from inspect import getmembers
import pprint
import random
import socket
import struct # for making packet headers into byte string
import threading 
import time

class RTPSocket:

	#construct a new RTPSocket
	def __init__(self):
		self.rtpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket_host = None
		self.socket_port = None
		self.N = 5
		
	#bind the socket passed in with the desired host and port (SERVER)
	def bind(self, source_address):
		self.socket_host = source_address[0]
		self.srcport = source_address[1]
		self.rtpsocket.bind(source_address)
		
	#connect to the desired host and port (CLIENT)
	def connect(self, destination_address):
		#client side 3 way handshake
		self.dsthost = destination_address[0]
		self.dstport = destination_address[1]

		client_isn = random.randint(0,9999)
		#srcport = self.socket_port; # Is this right?
		self.srcport = client_isn
		
		#header = RTPHeader(self.srcport, self.dstport, client_isn, 0, 0, 1, 0, 0, 0, 0)
		#packet = RTPPacket(header, "")

		
	
		#send packet with SYN=1 and seq=client_isn
		print "Sending SYN Packet"
		self.sendSYN(self.srcport, self.dstport, client_isn, destination_address)
		#self.send(packet.makeBytes(), destination_address)

		#wait to recieve a SYNACK from the server
		print "Waiting for SYNACK"
		while 1:
			data,addr = self.rtpsocket.recvfrom(1000)
			if data:
				header = self.getPacket(data).header
				if header.acknum == (client_isn + 1) and header.ACK == 1 and header.SYN == 1:
					print "Recieved SYNACK"
					break

		server_isn = header.seqnum
		acknum = server_isn + 1
		srcport = header.dest_port

		#header = RTPHeader(self.srcport, self.dstport, 0 + 1,  acknum, 1, 0, 0, 0, 0, 0)
		#packet = RTPPacket(header, "")

		print "Sending ACK"
		#self.send(packet.makeBytes(), destination_address)
		self.sendACK(self.srcport, self.dstport, server_isn, acknum, addr)
		#self.socket_port = self.srcport #?

	#server side of 3 way handshake
	def accept(self):
		# "listen" for SYN from client
		while 1:
			print "waiting..."
			data, dstaddr = self.rtpsocket.recvfrom(1000)
			if data:
				print "Received SYN Packet"
				header = self.getPacket(data).header
				if header.SYN == 1:
					break

		client_isn = header.seqnum
		self.dsthost = dstaddr[0]
		self.dstport = dstaddr[1]
		#generate a random server init number
		server_isn = random.randint(0,1000)
		acknum = client_isn + 1
		srcport = header.dest_port

		#header = RTPHeader(self.socket_port, self.dstport, server_isn, acknum, 1, 1, 0, 0, 0, 0)
		#packet = RTPPacket(header, "")
	
		#send packet with SYN=1 and seq=client_isn
		print self.socket_port
		print "^ PORT"
		self.sendSYNACK(self.srcport, self.dstport, client_isn + 1, server_isn, dstaddr)
		print "Sent SYNACK"
		#use seperate functions here
		#self.send(packet.makeBytes(), dstaddr)

		#wait to recieve a response from the client
		while 1:
			data, dstaddr = self.rtpsocket.recvfrom(1000)
			if data:
				
				header = self.getPacket(data).header
				print "Received ACK with seqnum " + str(header.seqnum) + ", acknum " + str(header.acknum)
				print "Expected: " + str(client_isn + 1) + ", " + str(server_isn + 1)
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

		for d in range(len(dataSegments)):
			#create a packet
			source_port = self.srcport
			dest_port = addr[1] #addr = (host,port)
			acknum = 0
			ACK = 0
			SYN = 0 
			FIN = 0 
			rwnd = 0 
			checksum = 0
			# if this is the last data segment, set eom = 1 in packet header
			if d == len(dataSegments) - 1:
				header = RTPHeader(source_port, dest_port, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, 1)
			else:
				header = RTPHeader(source_port, dest_port, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, 0)
			packet = RTPPacket(header, dataSegments[d])
			packetList.append(packet.makeBytes())
			seqnum = seqnum + 1

		#now we have to send the packet list (only send N)
		base = 0 
		nextseqnum = 0
		#self.timer_ran_out = False
		
		t = threading.Timer(RTPPacket.RTT, self.timeout, [base, nextseqnum])
		while len(packetList) != 0:
			if(nextseqnum < base + self.N):
				self.rtpsocket.sendto(packetList.pop(nextseqnum), addr)
				if(base == nextseqnum):
					t = threading.Timer(RTPPacket.RTT, self.timeout, [base, nextseqnum])
					t.start()
				nextseqnum = nextseqnum + 1
			#else: refuse data
			
			#timer
			# if self.timer_ran_out:
			# 	t = threading.Timer(RTPPacket.RTT, self.timeout, [base, nextseqnum])
			# 	t.start()
			# 	for i in range(base, nextseqnum - 1):
			# 		self.rtpsocket.sendto(packetList.pop(i), addr)
			# 	self.timer_ran_out = False

			#check for response ACKS
			response, dstaddr = self.rtpsocket.recvfrom(1000)
			if response: ## and its not corrupt
				responseHeader = self.getPacket(response).header
				base = responseHeader.acknum + 1
				if(base == nextseqnum):
					t.cancel()
				else:
					t = threading.Timer(RTPPacket.RTT, self.timeout, [base, nextseqnum])
					t.start()

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
	def timeout(self, base, nextseqnum):
		#self.timer_ran_out = True
		t = threading.Timer(RTPPacket.RTT, self.timeout, [base, nextseqnum])
		t.start()
		for i in range(base, nextseqnum - 1):
			self.rtpsocket.sendto(packetList.pop(i), addr)
			#self.timer_ran_out = False
		# instead of this just have it re-send packets


	# send a SYN
	def sendSYN(self, srcport, dstport, seqnum, addr):
		# make SYN packet
		header = RTPHeader(srcport, dstport, seqnum, 0, 0, 1, 0, 0, 0, 1)
		packet = RTPPacket(header, "")
		print packet
	
		#send packet with SYN=1 and seq=0 (change this)
		#print "Sending SYN Packet"
		self.rtpsocket.sendto(packet.makeBytes(), addr)
		print "Sent SYN"

	# send an ACK
	def sendACK(self, srcport, dstport, seqnum, acknum, addr):
		# make ACK packet
		header = RTPHeader(int(srcport), int(dstport), seqnum, acknum, 1, 0, 0, 0, 0, 1) # CHANGE THIS not the right seqnum, acknum etc
		packet = RTPPacket(header, "")
	
		#send packet with ACK=1 and seq=0 (change this)
		print "Sending ACK"
		self.rtpsocket.sendto(packet.makeBytes(), addr)

	# send a SYNACK
	def sendSYNACK(self, srcport, dstport, seqnum, acknum, addr):
		# make SYNACK packet
		header = RTPHeader(srcport, dstport, seqnum, acknum, 1, 1, 0, 0, 0, 1) # CHANGE THIS not the right seqnum, acknum etc
		packet = RTPPacket(header, "")
	
		#send packet with ACK=1 and SYN=1 and seq=0 (change this)
		print "Sending SYNACK"
		self.rtpsocket.sendto(packet.makeBytes(), addr)

	# send a FIN
	def sendFIN(self):
		# make FIN packet
		header = RTPHeader(self.socket_port, self.dstport, 0, 0, 0, 0, 1, 0, 1)
		packet = RTPPacket(header, "")
	
		#send packet with FIN=1 and seq=0 (change this)
		print "Sending FIN Packet"
		self.send(packet.makeBytes(), (self.dsthost, self.dstport))

	# receive data at a socket
	# returns data, addr
	def recv(self):
		print "Calling recv"
		expectedseqnum = 0
		data_received = "" # received data as string
		end_of_message = False # need to implement eom

		while end_of_message == False:
			# receive a packet from sender
			response = self.rtpsocket.recvfrom(1000) # replace with rwnd
			print response
			rcvpkt = self.getPacket(response[0])
			rcv_address = response[1]
			rcv_port = rcv_address[1]
			
			# if packet with expected seqnum (in order) is received:
			if rcvpkt.header.seqnum == expectedseqnum:
				# set end_of_message = True if eom = 1 in packet header
				if rcvpkt.header.eom == 1:
					end_of_message = True
				# extract data - add onto string
				data_received += rcvpkt.data
				# send an ACK for the packet and increment expectedseqnum
				print "sending ACK for packet in recv"
				self.sendACK(self.srcport, rcv_port, rcvpkt.header.seqnum, rcvpkt.header.acknum, rcv_address)
				expectedseqnum += 1

			# else: re-send ACK for most recently received in-order packet
			else:	
				print "re-sending ACK for packet in recv"
				self.sendACK(self.srcport, rcv_port, rcvpkt.header.seqnum, rcvpkt.header.acknum, rcv_address)
				# if end_of_message was found, set it back to False 
				#end_of_message = False

		# when end of message is reached, return the data
		return data_received, rcv_address

		#return self.rtpsocket.recvfrom(1000) # for testing only

	# close the socket - the way TCP does it
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
				print "Did not receive ACK packet - socket timed out." # keep waiting I guess? for now

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
				print "Did not receive FIN - socket timed out."

		# send another ACK to the server... -____-
		self.sendACK(0) # using 0 as seqnum
		print "Received FIN from server, sent ACK"

		# wait a while to make sure the ACK gets received
		time.sleep(5) # 5 is placeholder - should be 2 * MSL

		# finally close the connection
		print "Closing Connection"
		self.rtpsocket.close()

	# takes in the byte string received and parses it
	# returns an RTPPacket
	def getPacket(self, bytes):
		n = struct.unpack("!H", bytes[:2]) # length of data string
		data_size = n[0] # get number from tuple
		unpack_fmt = '!HHHLLBBBHHB' + str(data_size) + 's' # header format + s * data_size
		tup = struct.unpack(unpack_fmt, bytes) # unpacks the packet into a tuple

		# now make new RTPPacket object with info from the tuple
		header = RTPHeader(tup[1], tup[2], tup[3], tup[4], tup[5], tup[6], tup[7], tup[8], tup[9], tup[10])
		packet = RTPPacket(header, tup[11])
		return packet

	def printSocket(self):
		return "Socket at Port: " + str(self.socket_port)

	def setTimeout(self, time):
		self.rtpsocket.settimeout(2)


class RTPPacket:

	MSS = 5 #5 bytes
	RTT = 2 # placeholder

	def __init__(self, header, data=""):
		self.header = header
		self.data = data
		self.isACKED = False
		self.isSent = False

	# string representation of a packet
	def __str__(self):
		return "Header: " + str(self.header) + ", Data: " + self.data


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

	def __init__(self, source_port, dest_port, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, eom):
		self.source_port = source_port
		self.dest_port = dest_port
		self.seqnum = seqnum
		self.acknum = acknum
		self.ACK = ACK
		self.SYN = SYN
		self.FIN = FIN
		self.rwnd = rwnd
		self.checksum = checksum
		self.eom = eom # 1 if end of message, 0 otherwise

	# string representation, allows you to see header fields if you print the header
	def __str__(self):
		return ("srcport: " + str(self.source_port) + ", destport: " + str(self.dest_port) + ", seqnum: " + str(self.seqnum) + ", acknum: " + str(self.acknum) + ", ACK: " + str(self.ACK) + ", SYN: "
			+ str(self.SYN) + ", FIN: " + str(self.FIN) + ", rwnd: " + str(self.rwnd) + ", checksum: " + str(self.checksum) + ", eom: " + str(self.eom))

	# packs header into bytes
	# added new len_data argument so we know the length of the data when we unpack
	def makeHeader(self, len_data = 0):
		return struct.pack('!HHHLLBBBHHB', len_data, self.source_port, self.dest_port, self.seqnum, self.acknum, self.ACK, self.SYN, self.FIN, self.rwnd, self.checksum, self.eom)
