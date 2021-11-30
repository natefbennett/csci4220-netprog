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

	control_addr = sys.argv[1]
	control_port = sys.argv[2]
	sensor_id    = sys.argv[3]
	sensor_range = sys.argv[4]
	init_x_pos   = sys.argv[5]
	init_y_pos   = sys.argv[6]

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
