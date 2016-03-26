"""
This module includes RTPSocket, RTPPacket, and RTPHeader classes.
"""
import random
import socket
import struct
import threading 
import time


class RTPSocket:
	"""Represents a socket using RTP."""

	def __init__(self):
		"""Constructs a new RTPSocket."""
		self.rtpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket_host = None
		self.socket_port = None
		#self.dsthost = None
		#self.dstport = None
		self.N = 5
		self.rwnd = None
		

	def bind(self, source_address):
		"""
		Binds the socket with the desired host and port.
		source_address: tuple (host, port)
		"""
		self.socket_host = source_address[0]
		self.socket_port = source_address[1]
		self.rtpsocket.bind(source_address)
		

	def connect(self, destination_address):
		"""
		Connects to the desired host and port
		destination_address: tuple (host, port)
		"""
		#client side 3 way handshake
		#self.dsthost = destination_address[0]
		dstport = destination_address[1]

		# client isn for 3 way handshake
		client_isn = random.randint(0,9999)

		#we dont know socket port yet, so set random number first
		self.socket_port = random.randint(0, 9999)
	
		#print "Sending SYN Packet with seqnum = " + str(client_isn)
		self.sendSYN(self.socket_port, dstport, client_isn, destination_address)

		#wait to recieve a SYNACK from the server
		while 1:
			data,addr = self.rtpsocket.recvfrom(1000)
			if data:
				header = self.getPacket(data).header
				if header.acknum == (client_isn + 1) and header.ACK == 1 and header.SYN == 1:
					#print "Recieved SYNACK"
					break

		server_isn = header.seqnum
		acknum = server_isn + 1

		#we recived a response that gives us our own socket port
		self.socket_port = header.dest_port

		self.sendACK(self.socket_port, dstport, client_isn + 1, acknum, addr)


	def accept(self):
		"""Server side of 3 way handshake; accepts connection to client."""
		# "listen" for SYN from client
		while 1:
			data, dstaddr = self.rtpsocket.recvfrom(1000)
			if data:
				#print "Received SYN"
				header = self.getPacket(data).header
				if header.SYN == 1:
					break

		client_isn = header.seqnum
		#self.dsthost = dstaddr[0]
		dstport = dstaddr[1]
		#generate a random server init number
		server_isn = random.randint(0,1000)
		acknum = client_isn + 1
		srcport = header.dest_port

		#print self.socket_port
		#print "Sending SYNACK with seqnum = " + str(server_isn + 1) + ", acknum = " + str(client_isn + 1)
		self.sendSYNACK(self.socket_port, dstport, server_isn, client_isn + 1, dstaddr)
		#print "Sent SYNACK"

		#wait to recieve a response from the client
		while 1:
			data, dstaddr = self.rtpsocket.recvfrom(1000)
			if data:
				header = self.getPacket(data).header
				#print "Received ACK with seqnum = " + str(header.seqnum) + ", acknum = " + str(header.acknum)
				#print "Expected: " + str(client_isn + 1) + ", " + str(server_isn + 1)
				if header.seqnum == (client_isn + 1) and header.acknum == (server_isn + 1) and header.ACK == 1 and header.SYN == 0:
					break

		return dstaddr

	def send(self, data, addr):
		"""
		Sends data through a socket to an address
		data: data to send to address
		address: tuple (host, port)
		"""
		#list to store the data pieces
		dataSegments = []

		#break up the data into size MSS 
		for segment in range(0, len(data), RTPPacket.MSS):
			if segment+RTPPacket.MSS > len(data): 							#if we go out of bounds:
				dataSegments.append(data[segment:]) 						#	append from segment to the end
			else:
				dataSegments.append(data[segment:segment+RTPPacket.MSS]) 	#	append segment

		self.packetList = []

		seqnum = 0 #initialize to 0
		for d in range(len(dataSegments)):
			#create a packet
			source_port = self.socket_port
			dest_port = addr[1] #addr = (host,port)
			acknum = 0
			ACK = 0
			SYN = 0 
			FIN = 0 
			rwnd = self.rwnd
			checksum = 0
			# if this is the last data segment, set eom = 1 in packet header
			if d == len(dataSegments) - 1:
				header = RTPHeader(source_port, dest_port, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, 1)
			else:
				header = RTPHeader(source_port, dest_port, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, 0)
			packet = RTPPacket(header, dataSegments[d])
			self.packetList.append(packet)
			seqnum = seqnum + 1

		self.base = 0 
		self.nextseqnum = 0
		ackLastPacket = False
		while ackLastPacket == False:
			if(self.nextseqnum < self.base + self.N):
				#if we do a pop, the index automatically changes, so just index the packet list
				packetToSend = self.packetList[self.nextseqnum]
				#print "SEND:"
				#print packetToSend
				self.rtpsocket.sendto(packetToSend.makeBytes(), addr)
				if(self.base == self.nextseqnum):
					t = threading.Timer(RTPPacket.RTT, self.timeout, [addr])
					t.start()
				self.nextseqnum = self.nextseqnum + 1
			#else: refuse data

			#check for response ACKS
			response, dstaddr = self.rtpsocket.recvfrom(1000)
			if response: ## and its not corrupt
				responseHeader = self.getPacket(response).header
				self.base = responseHeader.acknum + 1
				for i in range(0, self.base): #cumulative ACK
					self.packetList[i].isACKED = True
				if(self.base == self.nextseqnum):
					t.cancel()
				else:
					t = threading.Timer(RTPPacket.RTT, self.timeout, [addr])
					t.start()

			if self.packetList[-1].isACKED:
				ackLastPacket = True


	def recv(self):
		"""Receives data at a socket and returns data, address."""
		#print "Calling recv"
		expectedseqnum = 0
		data_received = "" # received data as string
		end_of_message = False # need to implement eom

		while end_of_message == False:
			# receive a packet from sender
			response, rcv_address = self.rtpsocket.recvfrom(1000) # replace with rwnd
			last_acknum_sent = None
			if response:
				rcvpkt = self.getPacket(response)
				rcv_port = rcv_address[1]
				#print "Received Packet:"
				#print rcvpkt
				# if packet with expected seqnum (in order) is received:
				if rcvpkt.header.seqnum == expectedseqnum:
					# set end_of_message = True if eom = 1 in packet header
					if rcvpkt.header.eom == 1:
						end_of_message = True
					# extract data - add onto string
					data_received += rcvpkt.data
					# send an ACK for the packet and increment expectedseqnum
					#print "sending ACK for packet in recv"
					seqnum = rcvpkt.header.acknum
					acknum = rcvpkt.header.seqnum
					self.sendACK(self.socket_port, rcv_port, seqnum, acknum, rcv_address)
					expectedseqnum = expectedseqnum + 1
					last_acknum_sent = acknum

				# else: re-send ACK for most recently received in-order packet
				else:
					#only re-send the ACK after we have sent one ACK
					if last_acknum_sent != None:
						#print "re-sending ACK for packet in recv"
						seqnum = rcvpkt.header.acknum
						acknum = last_acknum_sent
						self.sendACK(self.socket_port, rcv_port, seqnum, acknum, rcv_address)
						# if end_of_message was found, set it back to False 
						#end_of_message = False

		# when end of message is reached, return the data
		return data_received, rcv_address
		#return self.rtpsocket.recvfrom(1000) # for testing only


	def timeout(self, addr):
		""" 
		Retransmits packets from base to nextseqnum-1
		addr: tuple (host, port)
		"""
		t = threading.Timer(RTPPacket.RTT, self.timeout, [addr])
		t.start()
		for i in range(self.base, self.nextseqnum): #range doesnt include last value so take out the minus 1
			self.rtpsocket.sendto(self.packetList[i].makeBytes(), addr)


	def sendSYN(self, srcport, dstport, seqnum, addr):
		"""Sends a SYN packet with srcport, dstport, seqnum to addr."""
		# make SYN packet
		acknum = 0
		ACK = 0
		SYN = 1
		FIN = 0
		rwnd = self.rwnd
		checksum = 0
		eom = 1

		header = RTPHeader(srcport, dstport, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, eom)
		packet = RTPPacket(header, "")
		#print packet
		self.rtpsocket.sendto(packet.makeBytes(), addr)
		#print "Sent SYN"


	def sendACK(self, srcport, dstport, seqnum, acknum, addr):
		"""Sends an ACK packet with scrport, dstport, seqnum, acknum to addr."""
		# make ACK packet
		ACK = 1
		SYN = 0
		FIN = 0
		rwnd = self.rwnd
		checksum = 0
		eom = 1

		header = RTPHeader(srcport, dstport, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, eom) # CHANGE THIS not the right seqnum, acknum etc
		packet = RTPPacket(header, "")
		#print packet
		#print "Sending ACK"
		self.rtpsocket.sendto(packet.makeBytes(), addr)


	def sendSYNACK(self, srcport, dstport, seqnum, acknum, addr):
		"""Sends a SYNACK packet with scrport, dstport, seqnum, acknum to addr"""
		# make SYNACK packet
		ACK = 1
		SYN = 1
		FIN = 0
		rwnd = self.rwnd
		checksum = 0
		eom = 1

		header = RTPHeader(srcport, dstport, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, eom) # CHANGE THIS not the right seqnum, acknum etc
		packet = RTPPacket(header, "")
	
		#print packet
		#print "Sending SYNACK"
		self.rtpsocket.sendto(packet.makeBytes(), addr)


	def sendFIN(self):
		"""Sends a FIN packet to (self.dsthost, self.dstport)"""
		# make FIN packet
		seqnum = 0
		acknum = 0
		ACK = 0
		SYN = 0
		FIN = 1
		rwnd = self.rwnd
		checksum = 0
		eom = 1

		header = RTPHeader(self.socket_port, self.dstport, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, eom)
		packet = RTPPacket(header, "CLOSE CONNECTION")
	
		#print packet
		#print "Sending FIN Packet"
		self.rtpsocket.sendto(packet.makeBytes(), (self.dsthost, self.dstport))


	def clientClose(self):
		"""Closes the RTP connection from the client side."""
		# send FIN to server
		self.sendFIN()
		#print "Sent FIN Packet"
		
		# wait for ACK from server
		self.setTimeout()
		while 1:
			try:
				data, addr = self.rtpsocket.recvfrom(1000)
				if data:
					if self.getPacket(data).isACK:
						#print "Received ACK"
						break

			except socket.error: #socket.error
				print "Did not receive ACK packet - socket timed out." # keep waiting I guess? for now
				return

		# wait for server to close (wait for FIN)
		self.setTimeout()
		while 1:
			try:
				data, addr = self.rtpsocket.recvfrom(1000)
				if data:
					if self.getPacket(data).isFIN:
						#print "Received FIN"
						break
			except socket.error:
				print "Did not receive FIN - socket timed out."
				return

		# send another ACK to the server... -____-
		dstaddr = (self.dsthost, self.dstport)
		self.sendACK(self.socket_port, self.dstport, 0, 0, dstaddr) # using 0 as seqnum
		#print "Received FIN from server, sent ACK"

		# wait a while to make sure the ACK gets received
		time.sleep(2 * RTPPacket.RTT) # 5 is placeholder - should be 2 * MSL

		# finally close the connection
		print "Closing Connection"
		self.rtpsocket.close()


	def serverClose(self):
		"""Closes the RTP connection from the server side."""
		#print "Sending ACK to Client"
		#send ACK to client
		dstaddr = (self.dsthost, self.dstport)
		self.sendACK(self.socket_port, self.dstport, 0, 0, dstaddr)
		#print "Sending FIN to Client"
		#send FIN to client
		self.sendFIN()
		print "Closing Connection"
		self.rtpsocket.close()


	def getPacket(self, bytes):
		"""
		Takes in a byte string and parses it into header and data.
		Returns an RTPPacket.
		"""
		n = struct.unpack("!H", bytes[:2]) # length of data string
		data_size = n[0] # get number from tuple
		unpack_fmt = '!HHHLLBBBHHB' + str(data_size) + 's' # header format + s * data_size
		tup = struct.unpack(unpack_fmt, bytes) # unpacks the packet into a tuple

		# now make new RTPPacket object with info from the tuple
		header = RTPHeader(tup[1], tup[2], tup[3], tup[4], tup[5], tup[6], tup[7], tup[8], tup[9], tup[10])
		packet = RTPPacket(header, tup[11])
		return packet


	def __str__(self):
		"""Returns a string representation of an RTPSocket."""
		return "Socket at Port " + str(self.socket_port) + " is sending to " + str(self.dsthost) + ":" + str(self.dstport)


	def setTimeout(self):
		"""Sets socket timeout to 2 seconds."""
		self.rtpsocket.settimeout(2)


class RTPPacket:
	"""
	Represents an RTP packet.
	MSS: maximum segment size in bytes
	RTT: round trip time in seconds
	"""

	MSS = 1 #5 bytes
	RTT = 2 # placeholder

	def __init__(self, header, data=""):
		"""Given an RTPHeader and data (optional), constructs a new RTPPacket."""
		self.header = header
		self.data = data
		self.isACKED = False


	def __str__(self):
		"""Returns a string representation of an RTPPacket."""
		return "Header: " + str(self.header) + ", Data: " + self.data


	def makeBytes(self):
		"""
		Returns the RTPPacket as a byte string.
		len_data (int) will be used when client/server receives a packet so the length of the data is known.
		See: http://docs.python.org/2/library/struct.html
		"""
		len_data = len(self.data)
		packed_header = self.header.makeHeader(len_data)
		return packed_header + self.data # bytes + string


	def isACK(self):
		"""Returns True if packet is an ACK, False otherwise."""
		return self.header.ACK == 1


	def isSYN(self):
		"""Returns True if packet is a SYN, False otherwise."""
		return self.header.SYN == 1


	def isFIN(self):
		"""Returns True if packet is a FIN, False otherwise."""
		return self.header.FIN == 1


class RTPHeader:
	"""Represents a header for an RTPPacket."""

	def __init__(self, source_port, dest_port, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, eom):
		"""Constructs a new RTPHeader with the fields passed in."""
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


	def __str__(self):
		"""Returns a string representation of an RTPHeader."""
		return ("srcport: " + str(self.source_port) + ", destport: " + str(self.dest_port) + ", seqnum: " + str(self.seqnum) + ", acknum: " + str(self.acknum) + ", ACK: " + str(self.ACK) + ", SYN: "
			+ str(self.SYN) + ", FIN: " + str(self.FIN) + ", rwnd: " + str(self.rwnd) + ", checksum: " + str(self.checksum) + ", eom: " + str(self.eom))


	def makeHeader(self, len_data = 0):
		"""Packs header fields and returns a byte string."""
		return struct.pack('!HHHLLBBBHHB', len_data, self.source_port, self.dest_port, self.seqnum, self.acknum, self.ACK, self.SYN, self.FIN, self.rwnd, self.checksum, self.eom)