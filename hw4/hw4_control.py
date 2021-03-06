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

# multi connections without threading reference
# https://stackoverflow.com/questions/5308080/python-socket-accept-nonblocking

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
		self.connections   = dict() # socket object -> SensorInfo

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
		# self.sock.setblocking(0)
		# self.sock.settimeout(1)

	def Accept(self):
		client_sock, client_addr = self.sock.accept() # returns (socket, address)
		self.connections[client_sock] = SensorInfo(client_addr)

	# get a socket from an id
	def GetSocket(self, id):
		for sock, sensor in self.connections.items():
			if sensor.id == id:
				return sock
		return None

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

			# base station asking, only give directly connected base stations
			if req_node.type == 'base_station':
				for base_station_id in req_node.links:
					base_station = self.GetNode(base_station_id)
					reachable.append([base_station.id, base_station.x, base_station.y])

			# sensor looking for reachable base stations
			else:
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

	def NextNodes(self, id, dest_id):
		tmp_list = []
		for node_data in self.Reachable(id):
			cur_id, cur_x, cur_y = node_data
			dist = self.GetNode(cur_id).GetDistance(self.GetNode(dest_id)) # distance form destination node
			tmp_list.append((dist, cur_id))

		# sort temp list and pull ids only out
		tmp_list.sort()
		sorted_reachable = [tmp[1] for tmp in tmp_list]

		return sorted_reachable

	def BaseStationForwarder(self, next_id, orig_id, dest_id, hop_list):
		
		# find base station with id NextID
		for base_station in self.base_stations:
			if next_id == base_station.id:
				# message has reached destination base station
				if base_station.id == dest_id:
					print(f'{base_station.id}: Message from {orig_id} to {dest_id} successfully received.')
				else:
					next_nodes = self.NextNodes(base_station.id, dest_id)
					n_next_id = None
					hop_list.append(base_station.id)

					# destination is reachable, send there next
					if dest_id in next_nodes:
						n_next_id = dest_id
					else:
						# find next node that isnt already in hop list
						for id in next_nodes:
							if id not in hop_list:
								n_next_id = id
								break

					# started from this base station
					if orig_id == base_station.id:
						if n_next_id == dest_id:
							print(f'{base_station.id}: Sent a new message directly to {dest_id}.')
						else:
							print(f'{base_station.id}: Sent a new message bound for {dest_id}.')
					else:
						print(f'{base_station.id}: Message from {orig_id} to {dest_id} being forwarded through {base_station.id}')

					# all reachable sensors and base stations are already in hop list
					if n_next_id == None:
						print(f'{base_station.id}: Message from {orig_id} to {dest_id} could not be delivered.')
						return
					
					# check if we are sending to a sensor or a base station
					internal = True
					# if sensor send to socket
					if self.GetNode(n_next_id).type == 'sensor':
						msg = f'DATAMESSAGE {orig_id} {n_next_id} {dest_id} {len(hop_list)} {" ".join(hop_list)}'
						self.GetSocket(n_next_id).sendall(msg.encode('utf-8'))
						internal = False

					# if sending to base station, call function recursivly 
					if internal:
						self.BaseStationForwarder(n_next_id, orig_id, dest_id, hop_list)

				break
		

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

		inputs = [ sys.stdin, control.sock ] + list(control.connections.keys())

		# accept inputs from sensors and stdin
		ready = select.select(inputs, [], [])[0]

		# loop though ready for reading
		for sock in ready:
			# check for new connections, if new connection
			# select will include server (control) socket in ready
			if sock == control.sock:
				control.Accept()

			# read from stdin for commands
			elif sock == sys.stdin:
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
						control.connections[sock].id    = id
						control.connections[sock].x     = int(x)
						control.connections[sock].y     = int(y)
						control.connections[sock].range = int(range)

						# find reachable (within range) base stations and sensors
						reachable = control.Reachable(id)
						reachable_str = ''
						for node in reachable:
							reachable_str += ' '.join(map(str, node)) + ' '

						# send response: REACHABLE [NumReachable] [ReachableList]=[[[ID] [XPosition] [YPosition]], [...], ...]									  
						resp = f'REACHABLE {len(reachable)} {reachable_str}'
						sock.sendall(resp.encode('utf-8'))

					# DATAMESSAGE [OriginID] [NextID] [DestinationID] [HopListLength] [HopList]
					elif cmd == 'DATAMESSAGE':

						orig_id		 = msg.pop(0)
						next_id		 = msg.pop(0)
						dest_id		 = msg.pop(0)
						hop_list_len = int(msg.pop(0))
						hop_list     = []

						for hop in msg:
							hop_list.append(hop)

						# [NextID] is a sensor???s ID 
						# deliver the message to the destination
						if next_id in [ sensor.id for sensor in control.connections.values() ]:
							next_sock = control.GetSocket(next_id)
							resp = f'DATAMESSAGE {orig_id} {next_id} {dest_id} {hop_list_len} {" ".join(hop_list)}'
							next_sock.sendall(resp.encode('utf-8'))

						# [NextID] is a base station
						else:
							control.BaseStationForwarder(next_id, orig_id, dest_id, hop_list)
									
					# WHERE [SensorID/BaseID] 
					elif cmd == 'WHERE':
						id = msg.pop(0)
						x, y = control.Where(id)

						# send response: THERE [NodeID] [XPosition] [YPosition]
						resp = f'THERE {id} {x} {y}'
						sock.sendall(resp.encode('utf-8'))

				# client connection ended 
				else:
					del control.connections[sock]
					inputs.remove(sock)
					sock.close()
					print('DEBUG: connection closed by sensor')

if __name__ == '__main__':
	run()