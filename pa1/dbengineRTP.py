#RDT server for RDBA
import sys
import csv
from rtp import *

server_host = '0.0.0.0'
#extract server_port argument
server_port = int(sys.argv[1]);
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

s = rtp_socket()
rtp_bind(s, server_host, server_port)
#rtp_listen(s)
rtp_accept(s)
rtp_close(s)

# try:
# 	#INITIALIZATION
# 	s = rtp_socket()
# 	rtp_bind(s, server_host, server_port)
# 	#data, dstaddr = rtp_listen(s)
# 	rtp_accept(s)
# 	print "herse"

# 	#rtp_listen(s)
# 	#conn,addr = rtp_accept(s)
# 	#DATA TRANSFER
# 	#receive the query and cols
# 	#send the data back to the client
# 	while 1:
# 		#recieve the data from the client
# 		data,addr = rtp_recv(s)
# 		if not data:
# 			# if there is no data recieved, we stop listening
# 			break
# 		dataList = data.split(":") #split the query and cols by colon
# 		print header
# 		print query
# 		header = dataList[0].strip()
# 		query = dataList[1].strip()

# 		if query not in db.keys():
# 			# if the client requests an ID that we do not have, we send the error message
# 			rtp_send(s, "Error: ID " + query + " not in the database!", addr)
# 			continue
# 		cols = dataList[2].split(",") #cols are comma delimited
# 		#initialize our response
# 		response = "From server: "
# 		for col in cols:
# 			col = col.strip()
# 			if col == "first_name":
# 				response = response + col + ": " + db[query][0]
# 			elif col == "last_name":
# 				response = response + col + ": " + db[query][1]
# 			elif col == "quality_points":
# 				response = response + col + ": " + db[query][2]
# 			elif col == "gpa_hours":
# 				response = response + col + ": " + db[query][3]
# 			elif col == "gpa":
# 				response = response + col + ": " + db[query][4]
# 			else:
# 				# if the client asks for a col that does not exist, we send the error message
# 				rtp_send(s, "Error: Client referring to a non-existing attribute - " + col, addr)
# 				continue
# 			if col != cols[len(cols) - 1].strip():
# 				response = response + ", " #do not add a comma for the last element
# 		rtp_send(s, response + "\n", addr)

# 	#TERMINATION
# 	#This is unreachable becuase crtl-c does not terminate the while loop, instead you must close the window
# 	#rtp_close(s)
# except:
# 	#if we find an exception above, we print error message
# 	print "Error accessing the server, please try again"