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

# sensor class to store the current state and send required messages
class Sensor:
	
	def __init__(self, id, x, y, c_addr, c_port, range):
		self.id     = id
		self.x      = x
		self.y      = y
		self.c_addr = c_addr
		self.c_port = c_port
		self.c_sock = None
		self.range  = range

	def Connect(self):
		# Create the TCP socket, connect to the server
		self.c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# bind takes a 2-tuple, not 2 arguments
		self.c_sock.connect((self.c_addr, self.c_port))

	def Disconnect(self):
		self.c_sock.close()

	# offer optional perameters, incase there are no new coords to send
	def UpdatePosition(self, new_x=-1, new_y=-1):
		
		send_x = new_y
		send_y = new_x

		# if no position perameters passed, keep current position
		if new_x != -1 and new_y != -1:
			send_x = self.x
			send_y = self.y

		# send message to control server
		msg = f'UPDATEPOSITION {self.id} {self.range} {send_x} {send_y}'
		self.c_sock.sendall(msg.encode('utf-8'))

		# wait for reachable message to be recieved
		recv_msg = self.c_sock.recv(1024).decode('utf-8')

		# sort the reachable list by their [SensorID]/[BaseID]
		recv_list = recv_msg.split()
		if recv_list.pop(0) == 'REACHABLE':
			num_reachable = recv_list.pop(0)
			recv_list = recv_list.sort()

			print(f'{self.id}: After reading REACHABLE message, I can see: {recv_list}')
		else:
			# wrong message received
			pass
		
	def SendDataMessage(self, dest_id):
		# self.c_sock.sendall(send_string.encode('utf-8'))
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
	if len(sys.argv) != 4:
		print(f'Usage: python3 -u {sys.argv[0]} [control address] [control port] [SensorID] [SensorRange] [InitialXPosition] [InitialYPosition]')
		sys.exit(-1)

	control_addr = sys.argv[1]      # address control server can be found
	control_port = int(sys.argv[2]) # port control server can be found
	sensor_id    = sys.argv[3]
	sensor_range = sys.argv[4]
	init_x_pos   = sys.argv[5]
	init_y_pos   = sys.argv[6]

	control_addr = socket.gethostbyname(control_addr)

	# initialize object to manage server operations
	sensor = Sensor(sensor_id, init_x_pos, init_y_pos, control_addr, control_port, sensor_range)

	# connect to control server
	sensor.Connect()

	# TODO: send an UPDATEPOSITION message to control server

	# read form stdin for commands
	for line in sys.stdin:

		line = line.split()

		# user hit enter with no data
		if line == []: 
			PrintCommandMenu()
			continue 

		cmd = line.pop(0)

		# command: MOVE [NewXPosition] [NewYPosition]
		if cmd == 'MOVE':
			# causes the sensor to update its location to the x-coordinate
			# specified by [NewXPosition] and the y-coordinate specified by [NewYPosition].
			# The sensor should also send an UPDATEPOSITION command to the server
			pass

		# command: SENDDATA [DestinationID]
		elif cmd == 'SENDDATA':
			# causes the sensor to generate a new DATAMESSAGE with a destination of
			# [DestinationID]. The sensor should first send an UPDATEPOSITION message to the server to get an
			# up-to-date list of reachable sensors and base stations.
			pass

		# command: WHERE [SensorID/BaseID]
		elif cmd == 'WHERE':
			# to get the location of a particular base station or sensor ID from the control
			# server. It should not take any other actions until it gets a THERE message back from the server.
			pass

		# command: QUIT
		elif cmd == 'QUIT':
			# causes the client program to clean up any memory and any 
			# sockets that are in use, and then terminate.
			pass

if __name__ == '__main__':
	run()
