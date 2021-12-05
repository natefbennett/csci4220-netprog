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

	# sensors can only send or receive messages if both
	# the sender and receiver can reach each other
	def InRange(self, other_node):
		distance = self.GetDistance(other_node)
		if distance <= self.range and distance <= other_node.range:
			return (True, distance)
		return (False, distance)

class SensorInfo(Node):

	def __init__(self, addr):
		self.id    = None
		self.x     = -1
		self.y     = -1
		self.range = -1
		self.addr  = addr
		self.type  = 'sensor'

class BaseStation(Node):
	
	def __init__(self, id, x, y, num_links, links):
		self.id        = id
		self.num_links = num_links
		self.x         = x
		self.y         = y
		self.links     = links
		self.range     = float('inf')
		self.type      = 'base_station'

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

	# find a base station or sensor that matches passed id
	def GetNode(self, id):
		# check sensors
		for sensor in self.connections.values():
			if sensor.id == id:
				return sensor

		# check base stations
		for base_station in self.base_stations:
			if base_station.id == id:
				return base_station

		return None

	def Reachable(self, id):
		reachable = []
		req_node = self.GetNode(id) # get range data and more from requested sensor
		
		# control knows about requested sensor
		if req_node != None:
			# loop through sensors and store all in range
			for sensor in self.connections.values():
				in_range, dist = req_node.InRange(sensor)
				if in_range and sensor.id != id:
					reachable.append([sensor.id, sensor.x, sensor.y])

			# loop though base stations
			for base_station in self.base_stations:
				in_range, dist = req_node.InRange(base_station)
				if in_range and base_station.id != id:
					reachable.append([base_station.id, base_station.x, base_station.y])

		# no sensor found with given id
		else:
			print('DEBUG: error in Reachable(id={id}) node not found')
		
		# return [[[ID] [XPosition] [YPosition]], [...], ...]
		return reachable

	# lookup position of a base station or sensor
	def Where(self, id):
		node = self.GetNode(id)
		return (node.x, node.y)

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
			for sock in ready:

				# read form stdin for commands
				if sock == sys.stdin:
					line = sys.stdin.readline()
					line = line.split()

					# user hit enter with no data
					if line == []: 
						PrintCommandMenu()
						continue 

					cmd = line.pop(0)

					# command: QUIT
					if cmd == 'QUIT':
						# causes the server program to clean up any memory and any 
						# sockets that are in use, and then terminate.
						for active_sock in inputs: 
							inputs.remove(active_sock)
							active_sock.close()

						sys.exit(0)
				
				# socket is a sensor connection
				else:
					msg = sock.recv(1024).decode('utf-8')
					if msg:
						# process sensor message
						msg = msg.split()
						cmd = msg.pop(0)

						# UPDATEPOSITION [SensorID] [SensorRange] [CurrentXPosition] [CurrentYPosition]
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
							sock.sendall(resp.encode('utf8'))

						# DATAMESSAGE [OriginID] [NextID] [DestinationID] [HopListLength] [HopList]
						if cmd == 'DATAMESSAGE':
							# TODO: implement base station behavior
							# ** see bottom of page 4 and top of 5 for actions **
							orig_id		 = msg.pop(0)
							next_id		 = msg.pop(0)
							dest_id		 = msg.pop(0)
							hop_list_len = int(msg.pop(0))
							hop_list     = []

							for i in range(hop_list_len):
								hop_list.append(msg[i])

							# [NextID] is a sensor’s ID 
							# 		deliver the message to the destination
							# [NextID] is a base station
							# 		base station id matches destination id
							# 			print(f'[BaseID]: Message from [OriginID] to [DestinationID] succesfully received')
							# 		all reachable sensors and base stations are already in hop list
							# 			print(f'[BaseID]: Message from [OriginID] to [DestinationID] succesfully received')
							# 		else send another DATAMESSAGE to next_id (base station), add base station id to hop list and get new next id
							#			print(f'[BaseID]: Message from [OriginID] to [DestinationID] being forwarded through [BaseID]')
							# 		if [OriginID] is the current base station, and the [NextID] and [DestinationID] match
							# 			print(f'[BaseID]: Sent a new message directly to [DestinationID]')
							#		else if the [OriginID] is the current base station
							# 			print(f'[BaseID]: Sent a new message bound for [DestinationID]')

						# WHERE [SensorID/BaseID] 
						if cmd == 'WHERE':
							id = int(msg.pop(0))
							x, y = control.Where(id)

							# send response: THERE [NodeID] [XPosition] [YPosition]
							resp = f'THERE {id} {x} {y}'
							sock.sendall(resp.encode('utf8'))

					# client connection ended 
					else:
						del control.connections[sock]
						inputs.remove(sock)
						sock.close()
						print('DEBUG: connection closed by sensor')

if __name__ == '__main__':
	run()