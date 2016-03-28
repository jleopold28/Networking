PA 2 - Design and Implement a Reliable Transport Protocol
March 28, 2016

James Leopold	jleopold3@gatech.edu
Kate Unsworth	kunsworth@gatech.edu

---
FILES SUBMITTED

dbclientRTP.py	relational database client
dbengineRTP.py	relational database server
ftaclient.py		file transfer application client
ftaserver.py		file transfer application server
README.txt		readme
rtp.py			reliable transfer protocol source code
Sample.txt		sample output file
3251.jpg		image for file transfer application

Instructions for compiling and running programs:

---
DESIGN DOCUMENTATION

I. How RTP works
	A. Connection establishment
		RTP establishes a connection with a three-way handshake (similar to TCP). First the server must bind to a port and listen for a SYN from the client. The client requests a connection by sending a SYN to the server with seqnum=client_isn (a randomly generated integer). The server receives the SYN and sends a SYNACK to the client with seqnum=server_isn (randomly generated integer) and acknum=client_isn+1 to grant the connection. Last, the client replies with an ACK to acknowledge the connection. The ACK has seqnum=client_isn+1 and acknum=server_isn+1.

	B. Connection termination
		RTP terminates a connection with a four-way handshake (similar to TCP). Either the client or the server may initiate the connection termination. The endpoint terminating the connection first (endpoint A) sends a FIN to the other endpoint (B). B receives the FIN and replies to A with an ACK to acknowledge that the connection will be ended. A will close the connection when this ACK is received. B waits a few seconds for the ACK to be received, then closes the connection.

	C. Flow control
		RTP provides receiver window-based flow control using the Go-Back-N protocol. Window size, N, is static and is configured when the connection is set up. [more on this later]

	D. Duplicate packets

	E. De-multiplexing

	F. Byte-stream semantics
		RTP assigns sequence numbers to packets to make sure they are delivered in the correct order. When the RTP receiver receives a packet it sends an ACK to the sender with the acknum (acknowledgement number) indicating which packet the ACK is for. The receiver discards any packets where the sequence number is not equal to the expected sequence number. This prevents the receiver from receiving duplicate packets or out-of-order packets. [more later]

	G. Special values/parameters
		1. isACKed: 
			RTP packets have an isACKed value to indicate whether the sender has received an ACK indicating that the packet has been received.

		2. eom: 
			This stands for "end of message" and is a RTP header field. If eom=1, the packet is the last packet in a message so the receiver knows to return the message data to the application layer.

II. RTP header structure and header fields
	The RTP header consists of the following fields:
	+=============+==========+======+==================================+
	| Field       | Type     | Size | Description					   |
	+=============+==========+======+==================================+
	| len_data	  | integer  |  2 	| Length of packet data 		   |
	| source_port | integer	 |	2 	| Source port 					   |
	| dest_port   | integer	 |	2 	| Destination port 				   |
	| seqnum 	  | integer	 |	4	| Sequence number 				   |
	| acknum	  |	integer	 |	4 	| Acknowledgement number 		   |
	| ACK 		  |	integer  |	1 	| 1 if ACK, 0 otherwise 		   |
	| SYN 		  |	integer	 |	1 	| 1 if SYN, 0 otherwise 		   |
	| FIN 		  |	integer  |	1 	| 1 if FIN, 0 otherwise 		   |
	| rwnd 		  |	integer  |	2 	| Receive window size  			   |
	| checksum 	  |	integer  |	2 	| Checksum value 				   |
	| eom		  |	integer  |	1 	| 1 if end of message, 0 otherwise |
	+=============+==========+======+==================================+

	The struct library is used to "pack" the header as a binary string. The data string is concatenated onto the header before the packet is sent. When a packet is received, it is "unpacked" to retrieve the data and header fields. The "Size" column is the size of the packed field in bytes, so the total size of the RTP header is 22 bytes. Network byte order is always used.

III. Finite State Machine diagrams

IV. Programming interface
	A. class RTPHeader
	   	Represents a header for an RTPPacket.
	 
	 	Methods defined here:
		__init__(self, source_port, dest_port, seqnum, acknum, ACK, SYN, FIN, rwnd, checksum, eom)
		Constructs a new RTPHeader with the fields passed in.
		
		__str__(self)
		Returns a string representation of an RTPHeader.
		
		makeHeader(self, len_data=0)
		Packs header fields and returns a byte string.

	B. class RTPPacket
	   	Represents an RTP packet.
		MSS: maximum segment size in bytes
		RTT: round trip time in seconds
		 
		Methods defined here:
		__init__(self, header, data='')
		Given an RTPHeader and data (optional), constructs a new RTPPacket.
		
		__str__(self)
		Returns a string representation of an RTPPacket.
		
		isACK(self)
		Returns True if packet is an ACK, False otherwise.
		
		isFIN(self)
		Returns True if packet is a FIN, False otherwise.
		
		isSYN(self)
		Returns True if packet is a SYN, False otherwise.
		
		makeBytes(self)
		Returns the RTPPacket as a byte string.
		len_data (int) will be used when client/server receives a packet so the length of the data is known.
		See: http://docs.python.org/2/library/struct.html
		
		Data and other attributes defined here:
		MSS = 1
		RTT = 2

	C. class RTPSocket
   		Represents a socket using RTP.
 
 		Methods defined here:
		__init__(self)
		Constructs a new RTPSocket.
		
		__str__(self)
		Returns a string representation of an RTPSocket.
		
		accept(self)
		Server side of 3 way handshake; accepts connection to client.
		
		bind(self, source_address)
		Binds the socket with the desired host and port.
		source_address: tuple (host, port)
		
		clientClose(self)
		Closes the RTP connection from the client side.
		
		connect(self, destination_address)
		Connects to the desired host and port
		destination_address: tuple (host, port)
		
		getPacket(self, bytes)
		Takes in a byte string and parses it into header and data.
		Returns an RTPPacket.
		
		recv(self)
		Receives data at a socket and returns data, address.
		
		send(self, data, addr)
		Sends data through a socket to an address
		data: data to send to address
		address: tuple (host, port)
		
		sendACK(self, srcport, dstport, seqnum, acknum, addr)
		Sends an ACK packet with scrport, dstport, seqnum, acknum to addr.
		
		sendFIN(self)
		Sends a FIN packet to (self.dsthost, self.dstport)
		
		sendSYN(self, srcport, dstport, seqnum, addr)
		Sends a SYN packet with srcport, dstport, seqnum to addr.
		
		sendSYNACK(self, srcport, dstport, seqnum, acknum, addr)
		Sends a SYNACK packet with scrport, dstport, seqnum, acknum to addr
		
		serverClose(self)
		Closes the RTP connection from the server side.
		
		setTimeout(self)
		Sets socket timeout to 2 seconds.
		
		timeout(self, addr)
		Retransmits packets from base to nextseqnum-1
		addr: tuple (host, port)


V. Algorithmic descriptions of non-trivial RTP functions

---
KNOWN BUGS AND LIMITATIONS
