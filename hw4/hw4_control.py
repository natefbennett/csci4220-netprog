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

from os import remove
import sys
import socket 
import select
import math

# store methods shared by base stations and sensors
class Node:

	# get euclidean distance from passed node (other_node)
	def GetDistance(self, other_node):
		dx = (self.x - other_node.x)
		dy = (self.y - other_node.y)
		return math.sqrt(dx*dx + dy*dy)

	def InRange(self, other_node):
		distance = self.GetDistance(other_node)
		if distance <= self.range:
			return (True, distance)
		return (False, distance)

class SensorInfo(Node):

	def __init__(self, addr):
		self.id    = None
		self.x     = -1
		self.y     = -1
		self.range = -1
		self.addr  = addr

class BaseStation(Node):
	
	def __init__(self, id, x, y, num_links, links):
		self.id        = id
		self.num_links = num_links
		self.x         = x
		self.y         = y
		self.links     = links
		self.range     = float('inf')

class Control:
		
	def __init__(self, port):
		self.id            = 'control'
		self.port          = port
		self.sock          = None
		self.base_stations = []
		self.connections   = dict() # file_descriptor -> SensorInfo

	def ParseBaseStationFile(self, filename):
		f = open(filename, 'r')
		for line in f:
			info      = line.split()
			id        = info.pop(0)
			x         = int(info.pop(0))
			y         = int(info.pop(0))
			num_links = int(info.pop(0))
			self.base_stations.append(BaseStation(id, x, y, num_links, info))

	def Listen(self):
		# create a TCP socket and listen on it
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # fix socket in use error
		self.sock.bind(('',self.port))
		self.sock.listen(10)

	# find connected sensor that matches passed id
	def GetSensorData(self, sensor_id):
		for sensor in self.connections.values():
			if sensor.id == sensor_id:
				return sensor
		return None

	def Reachable(self, sensor_id):
		reachable = []
		req_sensor = self.GetSensorData(sensor_id) # get range data and more from requested sensor
		
		# control knows about requested sensor
		if req_sensor != None:
			# loop through sensors and store all in range
			for sensor in self.connections.values():
				in_range, dist = req_sensor.InRange(sensor)
				if in_range and sensor.id != sensor_id:
					reachable.append([sensor.id, sensor.x, sensor.y])

			# loop though base stations
			for base in self.base_stations:
				in_range, dist = req_sensor.InRange(base)
				if in_range and base.id != sensor_id:
					reachable.append([base.id, base.x, base.y])

		# no sensor found with given id
		else:
			print('DEBUG: error in Reachable(sensor_id={sensor_id}) sensor not found')
		
		# return [[[ID] [XPosition] [YPosition]], [...], ...]
		return reachable

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
		client_sock, client_addr = control.sock.accept() # returns (socket, address)
		control.connections[client_sock] = SensorInfo(client_addr)
			
		inputs = [ sys.stdin ] + list(control.connections.keys())

		# accept inputs from control and stdin
		while True:
			ready = select.select(inputs, [], [])[0]

			# loop though ready file descriptors
			for fd in ready:

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
					msg = fd.recv(1024).decode('utf-8')
					if msg:
						# process sensor message
						msg = msg.split()
						cmd = msg.pop(0)

						if cmd == 'UPDATEPOSITION':
							id, range, x, y = msg

							# update control's store of sensor information
							control.connections[client_sock].id    = id
							control.connections[client_sock].x     = int(x)
							control.connections[client_sock].y     = int(y)
							control.connections[client_sock].range = int(range)

							# find reachable (within range) base stations and sensors
							reachable = control.Reachable(id)
							reachable_str = ''
							for node in reachable:
								reachable_str += ' '.join(map(str,node)) + ' '
							# send response: REACHABLE [NumReachable] [ReachableList]=[[[ID] [XPosition] [YPosition]], [...], ...]									  
							resp = f'REACHABLE {len(reachable)} {reachable_str}'
							fd.sendall(resp.encode('utf8'))

					# client connection ended 
					else:
						del control.connections[fd]
						print('DEBUG: connection closed by sensor')

if __name__ == '__main__':
	run()