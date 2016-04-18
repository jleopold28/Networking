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
	def __init__(self, destination_address):
		"""Constructs a new RTPConnection."""
		self.dst_addr = destination_address
		self.dst_host = destination_address[0]
		self.dst_port = destination_address[1]
		self.isOff = True

		# Receiver window for flow control
		self.rwnd = None # will be initialized in connect

		# Congestion control variables
		self.cwnd = RTPPacket.MSS # initially set cwnd to 1 (this replaces self.N)
		self.ssthresh = 128 # this will be reset after first loss event

		self.data = ""

	def getData(self):
		if self.data:
			out = self.data
			self.data = ""
			return out
		else:
			return ""

	def addData(self, data):
		self.data += data

	def startConn(self):
		self.isOff = False

	def foo(self):
		if len(self.ackList) == 0:
			return False
		else:
			return True

	def getACK(self):
		a = self.ackList.pop(0) #remove the first element
		return a

	def addACK(self, p):
		self.ackList.append(p)


class RTPSocket:
	"""Represents a socket over RTP"""
	def __init__(self):
		"""Constructs a new RTPConnection."""
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)

		self.server_isn = None
		self.rwnd = None

		self.SYNqueue = []
		self.SYNACKqueue = []
		self.FINqueue = []

		self.connections = {}

		self.ackList = {}
		self.finList = {}
 
		self.connLock = threading.Lock()
		self.ackLock = threading.Lock()
		self.finLock = threading.Lock()
		self.synackLock = threading.Lock()
		self.synLock = threading.Lock()

		self.recvThread = threading.Thread(target = self.recv)
		self.recvThread.daemon = True # so the thread will exit when the program exits

		#self.sock.settimeout(2)

	def bind(self, socket_addr):
		self.socket_addr = socket_addr
		self.socket_host = socket_addr[0]
		self.socket_port = socket_addr[1]
		self.sock.bind(self.socket_addr)
		#print "starting recv thread"
		self.recvThread.start()

	def accept(self):
		"""Server side of 3 way handshake; accepts connection to client."""

		if len(self.SYNqueue) == 0: # no SYN bits recevied
			return ("","")
			#print "no SYN bits received"
		else:
			with self.synLock:
				synPacket, dstaddr = self.SYNqueue.pop(0) #remove first SYN
			header = synPacket.header

			#send synack for this packet ....
			#we got a SYN bit so set up the connection with this client
			self.server_isn = random.randint(0,1000)
			acknum = header.seqnum + 1

			self.sendSYNACK(self.socket_port, dstaddr, self.server_isn, acknum)
			#print "sent SYNACK to " + str(dstaddr)

			# accept is server side so I think we need to create the connection object at the client address
			# then in connect we already have the connection in self.connections and just need to set conn.isOff = False

			conn_id = (dstaddr[0], dstaddr[1])
			#conn_id = dstaddr[1] 				# now identify by the client port! #random.randint(0,100000)
			conn = RTPConnection(dstaddr)
			conn.rwnd = self.rwnd # set rwnd for the connection

			with self.connLock:
				self.connections[conn_id] = conn

			with self.ackLock:
				self.ackList[conn_id] = []
			with self.finLock:
				self.finList[conn_id] = []

			while True:
				if conn.isOff == False:
					break
			
			#print "CONNECTION IS ON"
			#print "Socket address:" + str(self.socket_addr)
			return conn, dstaddr


	def connect(self, destination_address):
		"""
		Connects to the desired host and port
		destination_address: tuple (host, port)
		"""
		#client side 3 way handshake

		# client isn for 3 way handshake
		client_isn = random.randint(0,9999)

		#we dont know socket port yet, so set random number first
		self.socket_port = random.randint(0, 9999)
	
		#print "Sending SYN Packet with seqnum = " + str(client_isn)

		self.sendSYN(self.socket_port, destination_address, client_isn)

		#print "sent SYN to " + str(destination_address) + ", waiting for SYNACK"

		self.recvThread.start() # NEW
		#print "waiting for SYNACK queue"
		while 1:
			if len(self.SYNACKqueue) == 0: # no SYN bits recevied
				continue
			else:
				with self.synackLock:
					synackPacket, fromaddr = self.SYNACKqueue.pop(0) #get first SYNACK
				header = synackPacket.header
				break

		#print "SYNACK received"
		
		self.socket_host = ""
		self.socket_port = header.dest_port
		self.socket_addr = (self.socket_host, self.socket_port)

		#print "Socket address:" + str(self.socket_addr)

		server_isn = header.seqnum
		seqnum = header.acknum
		acknum = server_isn + 1

		#we recived a response that gives us our own socket port
	
		self.sendACK(self.socket_port, destination_address, seqnum, acknum)

		conn = RTPConnection(destination_address)
		conn.rwnd = self.rwnd

		conn_id = (destination_address[0], destination_address[1])

		with self.connLock:		
			self.connections[conn_id] = conn

		with self.ackLock:
			self.ackList[conn_id] = []
		with self.finLock:
			self.finList[conn_id] = []

		conn.startConn()
		#print "returning RTP connection at " + str(conn_id)
		return conn


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

		self.packetList = [] #SEND BUFFER
		seqnum = 0 
		for d in range(len(dataSegments)):
			source_port = self.socket_port
			dest_port = addr[1]             #addr = (host,port)
			acknum = 0
			ACK = 0
			SYN = 0 
			FIN = 0 
			rwnd = int(self.rwnd)
			checksum = 0
			if d == len(dataSegments) - 1:
				header = RTPHeader(source_port, dest_port, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, 1)
			else:  # if this is the last data segment, set eom = 1 in packet header
				header = RTPHeader(source_port, dest_port, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, 0)
			packet = RTPPacket(header, dataSegments[d])
			packet.setChecksum()

			self.packetList.append(packet)
			seqnum = seqnum + 1

		t = None
		self.base = 0 
		self.nextseqnum = 0
		# keep congestion window smaller than receive window
		#if self.connections[addr].cwnd > self.connections[addr].rwnd:
		#	self.connections[addr].cwnd = self.connections[addr].rwnd

		# set the number of packets that can be sent
		self.N = min(self.connections[addr].rwnd / RTPPacket.MSS , self.connections[addr].cwnd / RTPPacket.MSS)


		while 1:
			while (self.nextseqnum < self.base + self.N) and self.nextseqnum < len(self.packetList):	
				#self.N = self.connections[addr].cwnd
				print "Sending packet, self.N = " + str(self.N)
				packetToSend = self.packetList[self.nextseqnum]
				#print "SND: " + str(packetToSend)
				#raw_input("press to send")
				
				self.sock.sendto(packetToSend.makeBytes(), addr)

				self.N = min(self.connections[addr].rwnd / RTPPacket.MSS, self.connections[addr].cwnd / RTPPacket.MSS)

				if(self.base == self.nextseqnum):
					if t != None: #is there is a timer running, stop it
						t.cancel()
					t = threading.Timer(RTPPacket.RTT, self.timeout, [addr])
					t.start()
				self.nextseqnum += 1

			if self.ackList[addr] != []:
				with self.ackLock: #lock becuase we are removing data
					packet = self.ackList[addr].pop(0)

				# increase cwnd because ACK was received
				if self.connections[addr].cwnd < self.connections[addr].ssthresh:
					self.connections[addr].cwnd = self.connections[addr].cwnd * 2
				else :                                  #self.connections[addr].cwnd < self.connections[addr].rwnd:
					self.connections[addr].cwnd = self.connections[addr].cwnd + RTPPacket.MSS

				print "Received ACK, cwnd: " + str(self.connections[addr].cwnd)
				header = packet.header
				self.base = header.acknum + 1
				for i in range(0, self.base): #cumulative ACK
					self.packetList[i].isACKED = True
				if(self.base == self.nextseqnum):
					t.cancel()
				else:
					if t != None:
						t.cancel()
					t = threading.Timer(RTPPacket.RTT, self.timeout, [addr])
					t.start()

			if self.packetList[-1].isACKED == True:
				if t != None:
					t.cancel()
				break

		#print "FINISHED SENDING MESSAGE"

	def timeout(self, addr):
		""" 
		Retransmits packets from base to nextseqnum-1
		addr: tuple (host, port)
		"""
		print "\nTIMEOUT\n"
		# loss event occurred, so reset ssthresh and cwnd

		self.connections[addr].ssthresh = self.connections[addr].cwnd / 2 # set to 1/2 initial value of cwnd
		self.connections[addr].cwnd = RTPPacket.MSS

		t = threading.Timer(RTPPacket.RTT, self.timeout, [addr])
		t.start()

		for i in range(self.base, self.nextseqnum): #range doesnt include last value so take out the minus 1
			packetToSend = self.packetList[i]
			self.sock.sendto(packetToSend.makeBytes(), addr)

	def recv(self):
		"""Receives data at a socket and returns data, address."""

		expectedseqnum = 0
		last_acknum_sent = None

		while True:
			response, rcv_address = self.sock.recvfrom(1000) # replace with rwnd

			if response:
				rcvpkt = self.getPacket(response)
				header = rcvpkt.header

				if header.ACK == 0 and header.SYN == 1 and header.checksum == rcvpkt.getChecksum(): #SYN
					with self.synLock:
						self.SYNqueue.append((rcvpkt, rcv_address)) #add to the SYN queue
					continue
				elif header.ACK == 1 and header.SYN == 1 and header.checksum == rcvpkt.getChecksum():  #SYNACK
					with self.synackLock:
						self.SYNACKqueue.append((rcvpkt, rcv_address))
					continue
				elif header.FIN == 1 and header.checksum == rcvpkt.getChecksum(): #FIN
					with self.finLock:
						self.finList[rcv_address].append(rcvpkt)
					continue
				elif self.server_isn != None and header.ACK == 1 and header.SYN == 0 and header.acknum == (self.server_isn + 1) and header.checksum == rcvpkt.getChecksum(): 
					with self.connLock:
						self.connections[rcv_address].startConn()
					self.server_isn = None
					continue
				elif rcvpkt and header.ACK == 1 and header.checksum == rcvpkt.getChecksum(): #GOT ACK
					with self.ackLock:
						self.ackList[rcv_address].append(rcvpkt)
					continue
				elif rcvpkt and header.ACK == 0 and header.checksum == rcvpkt.getChecksum(): #we got data AND not corrupt
					rcv_port = rcv_address[1]
					if rcvpkt.header.seqnum == expectedseqnum:
						with self.connLock:
							self.connections[rcv_address].addData(rcvpkt.data)
						seqnum = rcvpkt.header.acknum
						self.sendACK(self.socket_port, rcv_address, seqnum, expectedseqnum)
						last_acknum_sent = expectedseqnum

						if rcvpkt.header.eom == 1:
							expectedseqnum = 0	
						else:
							expectedseqnum += 1
					else:
						#only re-send the ACK after we have sent one ACK
						if last_acknum_sent != None:
							seqnum = rcvpkt.header.acknum
							self.sendACK(self.socket_port, rcv_address, seqnum, last_acknum_sent)


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
		packet.setChecksum()
		#print "SND: " + str(packet)
		self.sock.sendto(packet.makeBytes(), dstaddr)


	def sendACK(self, srcport, dstaddr, seqnum, acknum):
		"""Sends an ACK packet with scrport, dstport, seqnum, acknum to addr."""
		
		# REMOVE THIS - here to simulate dropped ACKs ============
		#rand = random.randint(0, 10)
		#if rand == 6:
		#	return
		# ========================================================

		dstport = dstaddr[1]
		ACK = 1
		SYN = 0
		FIN = 0
		rwnd = self.rwnd
		checksum = 0
		eom = 1

		header = RTPHeader(srcport, dstport, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, eom) # CHANGE THIS not the right seqnum, acknum etc
		packet = RTPPacket(header, "")
		packet.setChecksum()
		#print "SENT ACK: " + str(packet)
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
		packet.setChecksum()
	
		#print packet
		#print "SYNACK: "+ str(packet)
		self.sock.sendto(packet.makeBytes(), dstaddr)


	def sendFIN(self, srcport, dstaddr, seqnum, acknum):
		"""Sends a FIN packet to (self.dsthost, self.dstport)"""
		# make FIN packet
		dstport = dstaddr[1]
		ACK = 0
		SYN = 0
		FIN = 1
		rwnd = self.rwnd
		checksum = 0
		eom = 1

		header = RTPHeader(srcport, dstport, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, eom)
		packet = RTPPacket(header, "CLOSE CONNECTION")
		packet.setChecksum()
	
		#print packet
		#print "Sending FIN Packet"
		self.sock.sendto(packet.makeBytes(), dstaddr)


	def clientClose(self, conn):
		"""Closes the RTP socket and connection from the client side."""
		# send FIN to server
		addr = conn.dst_addr
		self.sendFIN(self.socket_port, addr, 0, 0)

		# wait for ACK from server
		#self.setTimeout()
		while 1:
			try:
				if self.ackList[addr] != []:
					with self.ackLock:
						packet = self.ackList[addr].pop(0) #lock becuase we are modifying data

					header = packet.header
					break
			except socket.error:
				print "Did not receive ACK packet - socket timed out." # keep waiting I guess? for now
				return

		# wait for FIN from server
		#self.setTimeout()
		while 1:
			try:
				# wait for FIN bit and pop from FIN queue]
				if self.finList[addr[1]] != []:
					with self.finLock:
						finPacket = self.finList[addr[1]].pop(0) # get first FIN but do not remove from queue
					header = finPacket.header
					break

			except socket.error:
				print "Did not receive FIN - socket timed out."
				return

		# send another ACK to the server... -____-
		self.sendACK(self.socket_port, addr, 0, 0) # using 0 as seqnum

		# wait a while to make sure the ACK gets received
		time.sleep(2) # placeholder - should be 2 * MSL

		# finally close the connection
		
		self.sock.close()


	def serverClose(self, conn):
		"""Closes the RTP connection passed in."""
		# wait for FIN
		#self.setTimeout()
		dstaddr = conn.dst_addr

		while 1:
			if self.finList[dstaddr] != []:
				with self.finLock:
					finPacket = self.finList[dstaddr].pop(0)
				header = finPacket.header
				break

		# send ACK
		self.sendACK(self.socket_port, dstaddr, 0, 0)

		# wait for app
		# ???

		# send FIN
		self.sendFIN(self.socket_port, dstaddr, 0, 0)

		# wait for ACK
		#self.setTimeout()
		while 1:
			if self.ackList[dstaddr] != []:
				with self.ackLock:
					packet = self.ackList[dstaddr].pop(0)
				header = packet.header
				break

		# close connection
		conn.isOff = True
		with self.connLock:
			del self.connections[dstaddr]# remove conn from self.connections


	def getPacket(self, bytes):
		"""
		Takes in a byte string and parses it into header and data.
		Returns an RTPPacket.
		"""
		n = struct.unpack("!H", bytes[:2]) # length of data string
		data_size = n[0] # get number from tuple
		unpack_fmt = '!HHHLLBBBHLB' + str(data_size) + 's' # header format + s * data_size
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

	MSS = 512   # FIXED PACKET SIZE 512 bytes
	RTT = 2     # TIMEOUT 2 S

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


	# http://www.binarytides.com/raw-socket-programming-in-python-linux/
	# http://locklessinc.com/articles/tcp_checksum/
	def getChecksum(self):
		"""Returns the checksum of a packet"""
		# TODO exclude checksum from the checksum calculation!
		pkt = self.header.makePseudoHeader() + self.data

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
		return int(csum)
		


	def setChecksum(self):
		"""Sets the checksum field in the RTPPacket header"""
		csum = self.getChecksum()
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
		return struct.pack('!HHHLLBBBHLB', len_data, self.source_port, self.dest_port, self.seqnum, self.acknum, self.ACK, self.SYN, self.FIN, self.rwnd, self.checksum, self.eom)


	def makePseudoHeader(self):
		"""Packs certain header fields into pseudo header to be used in checksum calculation."""
		return struct.pack('!HHLLBBBHB', self.source_port, self.dest_port, self.seqnum, self.acknum, self.ACK, self.SYN, self.FIN, self.rwnd, self.eom) 