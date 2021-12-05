#!/usr/bin/env python3

# Author(s): Nate Bennett, Anisha Halwai
# Date:      12/7/21
# File:      hw4_client.py
#
# Assignment 4: Mobile Sensor Network Relay
#
# CSCI 4220: Network Programming
# Professor Jasmine Plum
#
# Usage:  python3 -u hw4_client.py [control address] [control port] [SensorID] [SensorRange] [InitalXPosition] [InitialYPosition]

import sys
import socket
import select

# sensor class to store the current state and send required messages
class Sensor:
	
	def __init__(self, id, x, y, c_addr, c_port, range):
		self.id        = id
		self.x         = x
		self.y         = y
		self.c_addr    = c_addr
		self.c_port    = c_port
		self.c_sock    = None
		self.range     = range
		self.reachable = dict()

	def Connect(self):
		# Create the TCP socket, connect to the server
		self.c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# bind takes a 2-tuple, not 2 arguments
		self.c_sock.connect((self.c_addr, self.c_port))

	def Disconnect(self):
		self.c_sock.close()

	# offer optional perameters, incase there are no new coords to send
	def UpdatePosition(self, new_x=-1, new_y=-1):

		# position perameters passed, update sensor position
		if new_x != -1 and new_y != -1:
			self.x = new_x
			self.y = new_y

		# send message to control server
		msg = f'UPDATEPOSITION {self.id} {self.range} {self.x} {self.y}'
		self.c_sock.sendall(msg.encode('utf-8'))

		# wait for reachable message to be recieved
		recv_msg = self.c_sock.recv(1024).decode('utf-8')

		# sort the reachable list by their [SensorID]/[BaseID]
		recv_list = recv_msg.split()

		if recv_list.pop(0) == 'REACHABLE':

			# convert recieved data to list
			num_reachable  = int(recv_list.pop(0))
			reachable_data = recv_list
			reachable_dict = dict()
			i = 0
			while i < num_reachable*3:
				reachable_dict[reachable_data[i]] = {   
						  'x': reachable_data[i+1],
						  'y': reachable_data[i+2] 
				}
				i += 3 
		
			# update this sensors reachable dictionary
			self.reachable = reachable_dict

			# build string from sorted list of base station and sensor ids
			reachable_ids = list(self.reachable.keys())
			reachable_ids.sort()
			reachable_str = ' '.join(reachable_ids)
		
			print(f'{self.id}: After reading REACHABLE message, I can see: {reachable_str}')
		
		# wrong message received
		else:	
			pass
		
	def SendDataMessage(self, dest_id):
		next_id = None # find where to send
		hop_list = []  # ??
		# DATAMESSAGE [OriginID] [NextID] [DestinationID] [HopListLength] [HopList]
		msg = f'DATAMESSAGE {self.id} {next_id} {dest_id} {len(hop_list)} {hop_list}'
		self.c_sock.sendall(msg.encode('utf-8'))
		# get the response from the server
    	# recv_string = self.c_sock.recv(1024)
		pass

	def Where(self, id):
		pass


def PrintCommandMenu():
	print(
		'Available Commands:\n' + \
		'\tMOVE     [NewXPosition] [NewYPosition] \n' + \
		'\tSENDDATA [DestinationID]\n' + \
		'\tWHERE    [SensorID/BaseID]\n' + \
		'\tQUIT\n'
	)

def run():

	# check number of command line args
	if len(sys.argv) != 7:
		print(f'Usage: python3 -u {sys.argv[0]} [control address] [control port] [SensorID] [SensorRange] [InitialXPosition] [InitialYPosition]')
		sys.exit(-1)

	control_addr = sys.argv[1]      # address control server can be found
	control_port = int(sys.argv[2]) # port control server can be found
	sensor_id    = sys.argv[3]
	sensor_range = sys.argv[4]
	init_x_pos   = sys.argv[5]
	init_y_pos   = sys.argv[6]

	control_addr = socket.gethostbyname(control_addr)

	# initialize object to manage sensor operations
	sensor = Sensor(sensor_id, init_x_pos, init_y_pos, control_addr, control_port, sensor_range)

	# connect to control server
	sensor.Connect()

	# send an UPDATEPOSITION message to control server
	sensor.UpdatePosition()

	# accept inputs from control and stdin
	inputs = [ sys.stdin, sensor.c_sock ]
	while True:
		ready = select.select(inputs, [], [])[0]

		# read form stdin for commands
		if sys.stdin in ready:
			line = sys.stdin.readline()

			# check for exit
			if not line:
				break

			line = line.split()

			# user hit enter with no data
			if line == []: 
				PrintCommandMenu()
				continue 

			cmd = line.pop(0)

			# command: MOVE [NewXPosition] [NewYPosition]
			if cmd == 'MOVE':
				# sensor updates its location to the x-coordinate [NewXPosition]
				# and the y-coordinate specified by [NewYPosition].
				# send an UPDATEPOSITION command to the server
				new_x = line.pop(0)
				new_y = line.pop(0)
				sensor.UpdatePosition(new_x, new_y)

			# command: SENDDATA [DestinationID]
			elif cmd == 'SENDDATA':
				# first send an UPDATEPOSITION message to the server to get an
				# up-to-date list of reachable sensors and base stations.
				sensor.UpdatePosition()

				# sensor generates a new DATAMESSAGE with a destination [DestinationID]
				dest_id = line.pop(0)
				sensor.SendDataMessage(dest_id)

			# command: WHERE [SensorID/BaseID]
			elif cmd == 'WHERE':
				# to get the location of a particular base station or sensor ID from the control
				# server. It should not take any other actions until it gets a THERE message back from the server.
				pass

			# command: QUIT
			elif cmd == 'QUIT':
				# causes the client program to clean up any memory and any 
				# sockets that are in use, and then terminate.
				print('DEBUG: sensor closing connection to control')
				sensor.c_sock.close()
				break
		
		# read from control socket for messages
		if sensor.c_sock in ready:
			msg = sensor.c_sock.recv(1024).decode('utf-8')


if __name__ == '__main__':
	run()
