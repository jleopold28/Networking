"""
This module includes RTPSocket, RTPPacket, and RTPHeader classes.
"""
import random
import socket
import struct
import threading 
import time
import sys

class RTPConnection:
	"""Represents a connection over RTP"""
	def __init__(self, destination_address, socket_port, rwnd):
		"""Constructs a new RTPConnection."""
		self.socket_port = socket_port
		self.rwnd = rwnd
		self.dst_addr = destination_address
		self.dst_host = destination_address[0]
		self.dst_port = destination_address[1]
		self.isOff = True

		self.data = ""

	def getData(self):
		return self.data

	def addData(self, data):
		self.data += data

	def startConn(self):
		self.isOff = False

class RTPSocket:
	"""Represents a socket over RTP"""
	def __init__(self):
		"""Constructs a new RTPConnection."""
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)

		self.rwnd = None
		self.N = 5
		self.connections = {}
		self.SYNqueue = []
		self.SYNACKqueue = []

		self.lock = threading.Lock()
		self.recvThread = threading.Thread(target = self.recv)


	def bind(self, socket_addr):
		self.socket_addr = socket_addr
		self.socket_host = socket_addr[0]
		self.socket_port = socket_addr[1]
		#self.sock.close()
		self.sock.bind((self.socket_host, self.socket_port))
		print "starting recv thread"
		self.recvThread.start()

	def accept(self):
		"""Server side of 3 way handshake; accepts connection to client."""
		 #"listen" for SYN from client
		#print "calling accept"

		if len(self.SYNqueue) == 0: # no SYN bits recevied
			return "",""
			print "no SYN bits received"
		else:
			#get first SYN
			synPacket, dstaddr = self.SYNqueue[0]
			header = synPacket.header

			#send synack for this packet ....
			#we got a SYN bit so set up the connection with this client
			self.server_isn = random.randint(0,1000)
			acknum = header.seqnum + 1

			#self.sendSYNACK(self.socket_port, dstaddr, self.server_isn, acknum)
			#print "sent SYNACK to " + str(dstaddr)

			self.sendSYNACK(self.socket_port, dstaddr, self.server_isn, acknum)
			#print "sent SYNACK to " + str(dstaddr)


			# accept is server side so I think we need to create the connection object at the client address
			# then in connect we already have the connection in self.connections and just need to set conn.isOff = False
			conn_id = dstaddr[1] # now identify by the client port! #random.randint(0,100000)
			conn = RTPConnection(dstaddr, self.socket_port, self.rwnd)
			self.connections[conn_id] = conn

			#wait to recieve a response from the client
#<<<<<<< HEAD
#			print "connection is off"
#			while conn.isOff:
#				pass

#=======
			while True:
				if conn.isOff == False:
					break
			
			#print "CONNECTION IS ON"
#>>>>>>> 9714de190a7dc92b1b501a4785c192ec4d5f5646
			return conn, dstaddr
			
		# while 1:
		# 	data, dstaddr = self.sock.recvfrom(1024)
		# 	if data:
		# 		header = self.getPacket(data).header
		# 		if header.SYN == 1:
		# 			print "recved SYN"
		# 			break



	def connect(self, destination_address):
		"""
		Connects to the desired host and port
		destination_address: tuple (host, port)
		"""
		#client side 3 way handshake

		#dst_addr = destination_address
		#self.dst_host = destination_address[0]
		#self.dst_port = destination_address[1]

		#self.socket_addr = socket_addr
		#self.socket_host = socket_addr[0]
		#self.socket_port = socket_addr[1]

		# client isn for 3 way handshake
		client_isn = random.randint(0,9999)

		#we dont know socket port yet, so set random number first
		self.socket_port = random.randint(0, 9999)
	
		#print "Sending SYN Packet with seqnum = " + str(client_isn)
		self.sendSYN(self.socket_port, destination_address, client_isn)

		print "sent SYN to " + str(destination_address) + ", waiting for SYNACK"
		#wait to recieve a SYNACK from the server
		self.recvThread.start() # NEW
		#print "waiting for SYNACK queue"
		while 1:
			if len(self.SYNACKqueue) == 0: # no SYN bits recevied
				continue
			else:
				synackPacket, fromaddr = self.SYNACKqueue[0]
				#synackPacket = self.getPacket(synack)
				header = synackPacket.header
				print synackPacket
				#sys.exit(1)
				break
		print "SYNACK received"
		synackPacket, fromaddr = self.SYNACKqueue[0]
		header = synackPacket.header


		#self.socket_host = fromaddr[0]
		#self.socket_port = fromaddr[1]
		#self.socket_addr = (self.socket_host, self.socket_port)

		#self.socket_host = ""
		#self.socket_port = header.dest_port
		#self.socket_addr = (self.socket_host, self.socket_port)

		# self.sock.bind(self.socket_addr) # removed bc I don't think we need to bind on the client side?

		server_isn = header.seqnum
		seqnum = header.acknum
		acknum = server_isn + 1

		#we recived a response that gives us our own socket port
		#self.socket_port = header.dest_port
		self.sendACK(self.socket_port, destination_address, seqnum, acknum)

		#conn_id = destination_address #random.randint(0,100000)
		conn = RTPConnection(destination_address, self.socket_port, self.rwnd)
		conn_id = header.dest_port #destination_address #(self.socket_host, self.socket_port)
		#self.connections[conn_id] = conn
		#conn.isOff = False
		conn.startConn()
		print "returning RTP connection at " + str(conn_id)
		return conn


	def send(self, data, addr):
		print "Calling send with data:" + data + " to addr " + str(addr)
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

		self.packetList = []#this is our send buffer

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

		#print "len of packet list is " + str(len(self.packetList))
		print "PacketList: " + str(self.packetList)
		self.base = 0 
		self.nextseqnum = 0
		ackLastPacket = False
		while ackLastPacket == False:
			if(self.nextseqnum < self.base + self.N):
				#if we do a pop, the index automatically changes, so just index the packet list
				packetToSend = self.packetList[self.nextseqnum]
				print "SND: " + str(packetToSend)
				#raw_input("press to send")
				self.sock.sendto(packetToSend.makeBytes(), addr)
				if(self.base == self.nextseqnum):
					t = threading.Timer(RTPPacket.RTT, self.timeout, [addr])
					t.start()
				self.nextseqnum = self.nextseqnum + 1
			#else: refuse data

			#check for response ACKS
			#response, dstaddr = self.sock.recvfrom(1000)
			#response, dstaddr = self.recv()
			#packet = response[0]
			#header = getPacket(response).header
			#packet = self.getPacket(response)
			#header = packet.header
			#print packet
			#print header.ACK == 1
			#rint header.dest_port == self.socket_port
			elif self.packetList[-1].isACKED:
				ackLastPacket = True
			else:
				with self.lock:
					response, dstaddr = self.sock.recvfrom(1000)
				if response:
					packet = self.getPacket(response)
					header = self.getPacket(response).header

					if packet and header.ACK == 1 and header.dest_port == self.socket_port: ## and its not corrupt
						print "GOT: " + str(packet)
						#responseHeader = packet.header
						self.base = packet.header.acknum + 1
						#print "self base :" + str(self.base)
						for i in range(0, self.base): #cumulative ACK
							self.packetList[i].isACKED = True
						if(self.base == self.nextseqnum):
							t.cancel()
						else:
							t = threading.Timer(RTPPacket.RTT, self.timeout, [addr])
							t.start()

	def timeout(self, addr):
		""" 
		Retransmits packets from base to nextseqnum-1
		addr: tuple (host, port)
		"""
		t = threading.Timer(RTPPacket.RTT, self.timeout, [addr])
		t.start()
		for i in range(self.base, self.nextseqnum): #range doesnt include last value so take out the minus 1
			self.sock.sendto(self.packetList[i].makeBytes(), addr)

	def recv(self):
		"""Receives data at a socket and returns data, address."""
		#global data_buffer
		#data_buffer = ""
		#sock = self.sock
		while True:
			#response, rcv_address = self.sock.recvfrom(1000) # replace with rwnd
			#if response:
			#		for k in connections:
			#		if connections[k].dst_addr == rcv_address:
			#			connections[k].addRecvBuffer(self.getPacket(response))
			#else:
			#	continue
			expectedseqnum = 0
			last_acknum_sent = None
			end_of_message = False
			while end_of_message == False:

				with self.lock:
					response, rcv_address = self.sock.recvfrom(1000) # replace with rwnd
				if response:
					rcvkpt = self.getPacket(response)
					header = rcvkpt.header

					if header.ACK == 0 and header.SYN == 1: #just SNY
						self.SYNqueue.append((rcvkpt, rcv_address)) #add to the SYN queu
#<<<<<<< HEAD
						continue
					#if rcvpkt and header.source_port == self.dst_port:
					elif header.ACK == 1 and header.SYN == 0 and header.acknum == (self.server_isn + 1):   #START CONNECTION WITH ACK 
						print "starting connection at " + str(rcv_address)
						self.connections[rcv_address[1]].startConn()
					elif header.ACK == 1 and header.SYN == 1:  #GIT SYNACK
						self.SYNACKqueue.append((rcvkpt, rcv_address))
						return
					elif rcvkpt and header.dest_port == self.socket_port:
						rcv_port = rcv_address[1]
						print "RCV: " + str(rcvkpt)
#=======
						end_of_message = True
#					#if rcvpkt and header.source_port == self.dst_port:
#					elif header.ACK == 1 and header.SYN == 0 and header.acknum == (self.server_isn + 1):   #START CONNECTION WITH ACK 
#						print "GOT ACK FOR CONN START"
#						for c in self.connections:
#							if self.connections[c].dst_addr == rcv_address:
#									b = self.connections[c]
#									print b
#									b.startConn()
#						end_of_message = True
#
#					elif header.ACK == 1 and header.SYN == 1:  #GIT SYNACK
#						print "GOT SYNACK"
#						#print "GOT SYN ACK: " + str(rcvpkt)
#						self.SYNACKqueue.append((response, rcv_address))
#						end_of_message = True
#
#					elif rcvpkt and header.dest_port == self.socket_port:
#						rcv_port = rcv_address[1]
#						#print "RCV: " + str(rcvpkt)
#>>>>>>> 9714de190a7dc92b1b501a4785c192ec4d5f5646
						#rint expectedseqnum
						# if packet with expected seqnum (in order) is received:
						if rcvkpt.header.seqnum == expectedseqnum:
							# set end_of_message = True if eom = 1 in packet header
							if rcvkpt.header.eom == 1:
								end_of_message = True
							# extract data - add onto string
							self.connections[rcv_port].addData(rcvkpt.data)
							#data_buffer += rcvpkt.data

							#packets_received.append(rcvpkt)
							#data_received += rcvpkt.data
							# send an ACK for the packet and increment expectedseqnum
							#print "sending ACK for packet in recv"
							seqnum = rcvkpt.header.acknum
							acknum = rcvkpt.header.seqnum + 1
							self.sendACK(self.socket_port, rcv_address, seqnum, acknum)
							#expectedseqnum = expectedseqnum + 1
							expectedseqnum = acknum
							last_acknum_sent = acknum
						# else: re-send ACK for most recently received in-order packet
						else:
							#only re-send the ACK after we have sent one ACK
							if last_acknum_sent != None:
								#print "re-sending ACK for packet in recv"
								seqnum = rcvkpt.header.acknum
								acknum = last_acknum_sent
								self.sendACK(self.socket_port, rcv_address, seqnum, acknum)
								# if end_of_message was found, set it back to False 
								#end_of_message = False

		#data_buffer += "END OF FILE"
		# when end of message is reached, return the data
		#return data_buffer, rcv_address
		#return self.rtpsocket.recvfrom(1000) # for testing only


	def sendSYN(self, srcport, dstaddr, seqnum):
		"""Sends a SYN packet with srcport, dstport, seqnum to addr."""
		# make SYN packet
		dstport = dstaddr[1]
		acknum = 0
		ACK = 0
		SYN = 1
		FIN = 0
		rwnd = self.rwnd
		checksum = 0
		eom = 1

		header = RTPHeader(srcport, dstport, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, eom)
		packet = RTPPacket(header, "")
		#print "SND: " + str(packet)
		self.sock.sendto(packet.makeBytes(), dstaddr)


	def sendACK(self, srcport, dstaddr, seqnum, acknum):
		"""Sends an ACK packet with scrport, dstport, seqnum, acknum to addr."""
		# make ACK packet
		dstport = dstaddr[1]
		ACK = 1
		SYN = 0
		FIN = 0
		rwnd = self.rwnd
		checksum = 0
		eom = 1

		header = RTPHeader(srcport, dstport, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, eom) # CHANGE THIS not the right seqnum, acknum etc
		packet = RTPPacket(header, "")
		#print "ACK: " + str(packet)
		self.sock.sendto(packet.makeBytes(), dstaddr)


	def sendSYNACK(self, srcport, dstaddr, seqnum, acknum):
		"""Sends a SYNACK packet with scrport, dstport, seqnum, acknum to addr"""
		# make SYNACK packet
		dstport = dstaddr[1]
		ACK = 1
		SYN = 1
		FIN = 0
		rwnd = self.rwnd
		checksum = 0
		eom = 1

		header = RTPHeader(srcport, dstport, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, eom) # CHANGE THIS not the right seqnum, acknum etc
		packet = RTPPacket(header, "")
	
		#print packet
		#print "SYNACK: "+ str(packet)
		self.sock.sendto(packet.makeBytes(), dstaddr)


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
		self.sock.sendto(packet.makeBytes(), (self.dsthost, self.dstport))


	def clientClose(self):
		"""Closes the RTP connection from the client side."""
		# send FIN to server
		self.sendFIN()
		#print "Sent FIN Packet"
		
		# wait for ACK from server
		self.setTimeout()
		while 1:
			try:
				#data, addr = self.rtpsocket.recvfrom(1000)
				data, addr = self.recvfrom()
				if data:
					if self.getPacket(data[0]).isACK:
						#print "Received ACK"
						break

			except socket.error: #socket.error
				print "Did not receive ACK packet - socket timed out." # keep waiting I guess? for now
				return

		# wait for server to close (wait for FIN)
		self.setTimeout()
		while 1:
			try:
				#data, addr = self.rtpsocket.recvfrom(1000)
				data, addr = self.recvfrom()
				if data:
					if self.getPacket(data[0]).isFIN:
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

	def close(self):
		self.sock.close()
		print "Closed Connection"


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
		return "Socket at Port " + str(self.socket_host) + ":" + str(self.socket_port) + " is sending to " + str(self.dst_host) + ":" + str(self.dst_port) + "  ID = " + str(self.cid) + "\n"



	def setTimeout(self):
		"""Sets socket timeout to 2 seconds."""
		self.sock.settimeout(2)


class RTPPacket:
	"""
	Represents an RTP packet.
	MSS: maximum segment size in bytes
	RTT: round trip time in seconds
	"""

	MSS = 500 #5 bytes
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


	# http://www.binarytides.com/raw-socket-programming-in-python-linux/
	# http://locklessinc.com/articles/tcp_checksum/
	def checksum(self):
		"""Returns the checksum of a packet"""
		pkt = self.makeBytes()
		# calculate checksum on header + data
		csum = 0 # initialize sum to 0
		# if packet length is odd, add padding 0 at end
		if len(pkt) % 2 == 1:
			pkt += "\0"
		# loop through characters 2 at a time and add all to csum
		for i in range(0, len(pkt), 2):
			csum += ord(pkt[i]) + (ord(pkt[i+1]) << 8)
		# fold and invert
		csum = (csum >> 16) + (csum & 0xFFFF)
		csum = csum + (csum >> 16)
		csum = ~csum & 0xFFFF


	def setChecksum(self):
		"""Sets the checksum field in the RTPPacket header"""
		csum = self.checksum()
		self.header.checksum = csum


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
		return ("srcport=" + str(self.source_port) + ", destport=" + str(self.dest_port) + 
			", seqnum: " + str(self.seqnum) + ", acknum=" + str(self.acknum) + ", ACK=" + str(self.ACK) + ", SYN="
			+ str(self.SYN) + ", FIN=" + str(self.FIN) + ", rwnd=" + str(self.rwnd) + ", checksum=" + str(self.checksum) + ", eom=" + str(self.eom))


	def makeHeader(self, len_data = 0):
		"""Packs header fields and returns a byte string."""
		return struct.pack('!HHHLLBBBHHB', len_data, self.source_port, self.dest_port, self.seqnum, self.acknum, self.ACK, self.SYN, self.FIN, self.rwnd, self.checksum, self.eom)