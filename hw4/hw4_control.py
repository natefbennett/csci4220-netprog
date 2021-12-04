#!/usr/bin/env python3

# Author(s): Nate Bennett, Anisha Halwai
# Date:      12/7/21
# File:      hw4_control.py
#
# Assignment 4: Mobile Sensor Network Relay
#
# CSCI 4220: Network Programming
# Professor Jasmine Plum
#
# Usage:  python3 -u hw4_control.py [control port] [base station file]

import sys
import socket 

class BaseStation:
	
	def __init__(self, id, x, y, num_links, links):
		self.id        = id
		self.num_links = num_links
		self.x         = x
		self.y         = y
		self.links     = links

class Control:
		
	def __init__(self, port):
		self.id            = 'control'
		self.port          = port
		self.sock          = None
		self.base_stations = []

	def ParseBaseStationFile(self, filename):
		f = open(filename, 'r')
		for line in f:
			info      = line.split()
			id        = info.pop(0)
			x         = info.pop(0)
			y         = info.pop(0)
			num_links = line.pop(0)
			self.base_stations.append(BaseStation(id, x, y, num_links, info))

	def Listen(self):
		self.sock.listen(10)

def PrintCommandMenu():
	print(
		'Available Commands:\n' + \
		'\tQUIT\n'
	)

def run():
	
	# check number of command line args
	if len(sys.argv) != 4:
		print(f'Usage: python3 -u {sys.argv[0]} [control port] [base station file]')
		sys.exit(-1)

	control_port      = sys.argv[1]
	base_station_file = sys.argv[2]

	# parse base station file into BaseStation objects, 
	# save BaseStations to list in Control object
	control = Control(control_port)
	control.ParseBaseStationFile(base_station_file)

	# listen for stdin and for data from all sensor sockets
	control.Listen()

	# read form stdin for commands
	for line in sys.stdin:

		line = line.split()

		# user hit enter with no data
		if line == []: 
			PrintCommandMenu()
			continue 

		cmd = line.pop(0)

		# command: QUIT
		if cmd == 'QUIT':
			# causes the client program to clean up any memory and any 
			# sockets that are in use, and then terminate.
			pass

if __name__ == '__main__':
	run()