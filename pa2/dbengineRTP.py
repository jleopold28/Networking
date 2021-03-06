#RDT server for RDBA
import sys
import csv
sys.path.insert(0,'..')
from rtp import *

sock = None
db = {}

def clientSession(conn_id,addr):
	print "STARTING CLIENT SESSION at " + str(addr)
	while 1:
		data = sock.getData(conn_id)
		if data:
			if data == "CLOSE CONNECTION":
				sock.serverClose(conn_id)
				print "CLOSEING SESSION FOR " + str(addr) + "\n"
				break
			elif data:
				thread = threading.Thread(target = response, args = (data, addr))
				thread.start()
				thread.join()

	return

def response(data, addr):
	dataList = data.split(":") #split the query and cols by colon
	query = dataList[0].strip()

	if query not in db.keys():
		# if the client requests an ID that we do not have, we send the error message
		sock.send("Error: ID " + query + " not in the database!", addr)
		return

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
			# if column is invalid: send error message instead
			response = "From server: Error: Client referring to a non-existing attribute - " + col
			sock.send(response, addr)
			return

		if col != cols[len(cols) - 1].strip():
				response = response + ", " #do not add a comma for the last element

	sock.send(response, addr)
	return

def main(argv):
	server_host = '127.0.0.1'
	server_port = int(argv[1])
	#initialize our database
	global db
	#db = {} #format of db: {'ID' : ['first_name', 'last_name', 'quality_points', 'gpa_hours', 'gpa']}

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
		global sock
		sock = RTPSocket() #create only 1 socket
		sock.rwnd = 512
		sock.bind((server_host, server_port))
		while 1:
			#check the SYN QUE in ACCEPT
			conn_id, addr = sock.accept()
			if (conn_id, addr) != ( "","" ):
				newthread = threading.Thread(target = clientSession, args = (conn_id, addr,))
				newthread.start()

		#TERMINATION
		#This is unreachable becuase crtl-c does not terminate the while loop, instead you must close the window
		#sock.serverClose()
	except Exception, e:
		#if we find an exception above, we print error message
		print "Error accessing the server, please try again"
		print e

if __name__ == "__main__":
    main(sys.argv)