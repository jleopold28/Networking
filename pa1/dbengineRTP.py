#UDP server
import socket
import sys
import csv

host = '0.0.0.0'
#extract port argument
port = int(sys.argv[1]);
#initialize our database
db = {}
#format of db: {'ID' : ['first_name', 'last_name', 'quality_points', 'gpa_hours', 'gpa']}

f = open("db.csv")
#open the csv file holding the data
reader = csv.reader(f);
headers = reader.next();
#read the csv file into db
for row in reader:
	db[str(row[0])] = [row[1], row[2], row[3], row[4], row[5]]
#close the db.csv file
f.close()

try:
	#INITIALIZATION
	#create a socket of UDP type
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	print "Socket Created"
	#bind the socket
	s.bind((host, port))
	print "Socket Bind Complete"

	#DATA TRANSFER
	#receive the query and cols
	#send the data back to the client
	while 1:
		#recieve the data from the client
		data,addr = s.recvfrom(1024)
		if not data:
			# if there is no data recieved, we stop listening
			break
		dataList = data.split(":") #split the query and cols by colon
		query = dataList[0]
		if query not in db.keys():
			# if the client requests an ID that we do not have, we send the error message
			s.sendto("Error: ID " + query + " not in the database!", addr)
			continue
		cols = dataList[1].split(",") #cols are comma delimited
		#initialize our response
		response = "From server: "
		for col in cols:
			col = col.strip()
			if col == "first_name":
				response = response + col + ": " + db[query][0]
			elif col == "last_name":
				response = response + col + ": " + db[query][1]
			elif col == "quality_points":
				response = response + col + ": " + db[query][2]
			elif col == "gpa_hours":
				response = response + col + ": " + db[query][3]
			elif col == "gpa":
				response = response + col + ": " + db[query][4]
			else:
				# if the client asks for a col that does not exist, we send the error message
				s.sendto("Error: Client referring to a non-existing attribute - " + col, addr)
				continue
			if col != cols[len(cols) - 1].strip():
				response = response + ", " #do not add a comma for the last element
		s.sendto(response + "\n", addr) #send the response back to the server

	#TERMINATION
	#This is unreachable becuase crtl-c does not terminate the while loop, instead you must close the window
	print "Closing connection"
	s.close()
except:
	#if we find an exception above, we print error message
	print "Error accessing the server, please try again"