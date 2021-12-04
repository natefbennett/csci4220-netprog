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
import select

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
		self.connections   = []

	def ParseBaseStationFile(self, filename):
		f = open(filename, 'r')
		for line in f:
			info      = line.split()
			id        = info.pop(0)
			x         = info.pop(0)
			y         = info.pop(0)
			num_links = info.pop(0)
			self.base_stations.append(BaseStation(id, x, y, num_links, info))

	def Listen(self):
		# create a TCP socket and listen on it
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind(('',self.port))
		self.sock.listen(10)

def PrintCommandMenu():
	print(
		'Available Commands:\n' + \
		'\tQUIT\n'
	)

def run():
	
	# check number of command line args
	if len(sys.argv) != 3:
		print(f'Usage: python3 -u {sys.argv[0]} [control port] [base station file]')
		sys.exit(-1)

	control_port      = int(sys.argv[1])
	base_station_file = sys.argv[2]

	# parse base station file into BaseStation objects, 
	# save BaseStations to list in Control object
	control = Control(control_port)
	control.ParseBaseStationFile(base_station_file)

	# listen for stdin and for data from all sensor sockets
	control.Listen()

	# server loop, accept incoming connections
	while True:
		client_sock = control.sock.accept()[0]
		control.connections.append(client_sock)
		inputs = [ sys.stdin ] + control.connections

		# accept inputs from control and stdin
		while True:
			ready = select.select(inputs, [], [])[0]
			
			# loop though ready file descriptors
			for fd in ready:
				print(fd)
				# read form stdin for commands
				if fd == sys.stdin:
					line = sys.stdin.readline()
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
				
				# file descriptor (fd) is a sensor connection
				else:
					msg = fd.recv(1024)

if __name__ == '__main__':
	run()