# FTA Client with interactive command window

# create a reliable connection with the FTA server
def connect(host, port, rwnd):
	pass


# download file1 from server and upload file2 to the server through the same RTP connection
def get_post(file1, file2):
	pass


# download file from server
def get(file):
	pass


def main(argv):

	disconnect = False

	while disconnect == False:
		command = raw_input("> ")
		if command == disconnect:
			disconnect = True
		elif "fta-client" in command:
			# arguments should be H:P W
			# H: the IP address or hostname of the FTA-server
            # P: the UDP port number of the FTA-server
     		# W: the receive window size at the FTA-client (in bytes)
			connect()
		elif "get-post" in command:
			# arguments should be F G
			# F: download file F from the server
			# G: upload file G to the server through same RTP connection
			get_post(f,g)
		elif "get" in command:
			# argument should be F
			# F: download file F from the server
			get(f)
		else:
			print "Invalid command."
  

if __name__ == "__main__":
    main(sys.argv[1:])

