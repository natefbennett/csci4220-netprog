#!/usr/bin/env python3

# Author(s): Nate Bennett, Anisha Halwai
# Date:      11/09/21
# File:      hw3.py
#
# Assignment 3: SimpleKad DHT Implementation
#
# CSCI 4220: Network Programming
# Professor Jasmine Plum

from concurrent import futures
import sys  # For sys.argv, sys.exit()
import socket  # for gethostbyname()

import grpc

import csci4220_hw3_pb2 as pb2
import csci4220_hw3_pb2_grpc as pb2_grpc


class KadImplServicer(pb2_grpc.KadImplServicer):
	"""Provides methods that implement functionality of a simple Kademlia server."""

	# Member Variables
	n = -1
	k = -1
	node = None  # this servers node info
	k_buckets = []
	hash_table = dict()

	def __init__(self, n, k, id, addr, port):

		# initialize k buckets
		self.k = k
		self.n = n
		for i in range(n):
			self.k_buckets.append([])

		# setup this servers node
		self.node = pb2.Node(
			id      = id,
			port    = int(port),
			address = addr
		)

	def PrintKBuckets(self):

		# loop through each k bucket and print its nodes
		# print oldest to newest
		for i, k_bucket in enumerate(self.k_buckets):
			line = f'{i}:'
			for node in reversed(k_bucket):
				line += f' {node.id}:{node.port}'

			print(line)

	def SearchBuckets(self, node):
		for i, bucket in enumerate(self.k_buckets):
			for j, cur_node in enumerate(bucket):
				if cur_node == node: 
					return ( True, i, j )

		return ( False, -1, -1 )

	def Distance(self, node):
		return self.node.id ^ node.id

	def DeleteNode(self, node):
		dist = self.Distance(node)

		# check [i,N) k-buckets
		for i in range(self.n):
			lowerbound = 2 ** i
			upperbound = 2 ** (i + 1)
			if lowerbound <= dist and dist < upperbound:
				if node in self.k_buckets[i]:
					index = self.k_buckets[i].index(node)
					deleted_node = self.k_buckets[i].pop(index)

					return True

		# Error handling: failure to delete node to a k-bucket
		return False

	# adds the provided node to a k bucket
	def AddNode(self, node):
		#only add k entries in a bucket
		dist = self.Distance(node)

		# check [i,N) k-buckets
		for i in range(self.n):
			lowerbound = 2 ** i
			upperbound = 2 ** (i+1)

			if lowerbound <= dist and dist < upperbound:
				if self.SearchBuckets(node)[0]:
					self.DeleteNode(node)

				self.k_buckets[i].append(node)

				# kick oldest seen node from bucket
				if len(self.k_buckets[i]) > self.k:
					self.k_buckets[i].pop(0)

				return True

		# Error handling: failure to add node to a k-bucket
		return False

	def makeNodeMostRecent(self, node):
		"""
		update k-buckets by adding the requester’s ID to be the most recently used
		remove node id from i'th k-bucket, appending node id again(change
		position to be last/most recently used node id)
		[<older entry>, <next oldest>, ... ,<newest entry>]
		"""
		self.DeleteNode(node)
		self.AddNode(node)

	def Get_k_closest(self, requested_id):
		allNodes_with_distance = [] # [ <dist, node>, <dist, node>, ... ]
		for buckets in self.k_buckets:
			for n in buckets:
				dist = int(n.id) ^ int(requested_id)
				dist_node = (dist,n)
				allNodes_with_distance.append(dist_node)

		allNodes_with_distance.sort()
		if len(allNodes_with_distance) >= self.k:
			return [x[1] for x in allNodes_with_distance[:self.k]]
		else:
			return [x[1] for x in allNodes_with_distance]
		
	def Get_k_closest_value(self,requested_id):
			allNodes_with_distance = []  # [ <dist, node>, <dist, node>, ... ]

			for buckets in self.k_buckets:
				for node in buckets:
					dist = int(node.id) ^ int(requested_id)
					dist_node = (dist, node)
					allNodes_with_distance.append(dist_node)

			allNodes_with_distance.sort()
			if len(allNodes_with_distance) >= self.k:
				return [x[1] for x in allNodes_with_distance[:self.k]]
			else:
				return [x[1] for x in allNodes_with_distance]

	# ------------------------------------------- #
	#  Remote Procedure Call (RPC) Methods Below  #
	# ------------------------------------------- #


	# RPC: FindNode(IDKey) returns (NodeList)
	def FindNode(self, request, context):
		# return the k closest nodes to the provided ID
		# may need to look in several k-buckets
		self.AddNode(request.node)
		closest_k = self.Get_k_closest(request.idkey)
		print(
			f'Serving FindNode({request.idkey}) request for {request.node.id}')

		return pb2.NodeList(
			responding_node = self.node,
			nodes           = closest_k
		)

	# RPC: FindValue(IDKey) returns (KV_Node_Wrapper)
	def FindValue(self, request, context):

		print(f'Serving FindKey({request.idkey}) request for {request.node.id}')

		# If the remote node has been told to store the key
		# before it responds with the key and the associated value.
		if self.hash_table.get(request.idkey) != None:
				
				value = self.hash_table.get(request.idkey)
				return pb2.KV_Node_Wrapper(
					responding_node = self.node,
					mode_kv         = True,
					kv              = pb2.KeyValue(
										node  = self.node,
										key   = request.idkey,
										value = value
									)
				)
		# If the remote node has not been told to store the key,
		# it will reply with the k closest nodes to the key.
		else:
			k_closest = self.Get_k_closest_value(request.idkey)
			return pb2.KV_Node_Wrapper(
					responding_node = self.node,
					mode_kv         = False,
					nodes           = k_closest
			)

	# RPC: Store(KeyValue) returns (IDKey)
	# warining: does not check for collisions
	def Store(self, request, context):
		
		print(f'Storing key {request.key} value "{request.value}"')
		self.hash_table[request.key] = request.value

		# update k_buckets, add requester's ID to be most recently used
		# only if store request from a remote node
		if request.node != self.node:
			self.AddNode(request.node)

		# returns the node that the key value pair was stored and the key
		return pb2.IDKey(
			node  = self.node,
			idkey = request.key
		)

	# RPC: Quit(IDKey) returns (IDKey)
	def Quit(self, request, context):

		for i, k_bucket in enumerate(self.k_buckets[:]):
			# check k buckets for requested node
			if request.node in k_bucket:
				print(f'Evicting quitting node {request.node.id} from bucket {i}')
				self.DeleteNode(request.node
				)
				return pb2.IDKey(
					node  = self.node,
					idkey = request.node.id
				)

		# node not found
		print(f'No record of quitting node {request.node.id} in k-buckets.')
		return None


def PrintCommandMenu():
	print(
		'Available Commands:\n' + \
		'\tBOOTSTRAP  <remote_hostname> <remote_port>\n' + \
		'\tFIND_NODE  <node_id>\n' + \
		'\tFIND_VALUE <key>\n' + \
		'\tSTORE      <key> <value>\n' + \
		'\tQUIT\n'
	)

def run():
	if len(sys.argv) != 4:
		print("Error, correct usage is {} [my id] [my port] [k]".format(
			sys.argv[0]))
		sys.exit(-1)

	local_id = int(sys.argv[1])
	port = str(int(sys.argv[2]))  # add_insecure_port() will want a string
	k = int(sys.argv[3])
	n = 4

	# setup server, runs in background
	# returns an instance of KadImplServicer
	hostname = socket.gethostname()  # gets this machine's host name
	ip_addr = socket.gethostbyname(hostname)  # IP address from this hostname

	server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
	servicer = KadImplServicer(n, k, local_id, ip_addr, port)

	pb2_grpc.add_KadImplServicer_to_server(servicer, server)
	server.add_insecure_port(f'[::]:{port}')
	server.start()

	# read form stdin for commands
	for line in sys.stdin:

		line = line.split()

		# user hit enter with no data
		if line == []: 
			PrintCommandMenu()
			continue 

		cmd = line.pop(0)

		# command: BOOTSTRAP <remote_hostname> <remote_port>
		if cmd == 'BOOTSTRAP':

			# validate usage
			if len(line) != 2:
				print('Usage: BOOTSTRAP <remote hostname> <remote port>')
				continue

			remote_hostname, remote_port = line
			remote_addr = socket.gethostbyname(remote_hostname)

			# send remote node a FindNode RPC using the local node's ID
			# add k closest nodes to this instances servicer as well as
			# the requested remote host's node
			with grpc.insecure_channel(f'{remote_addr}:{remote_port}') as channel:
				stub = pb2_grpc.KadImplStub(channel)

				# FindNode returns k closest nodes to this clients node
				node_list = stub.FindNode(pb2.IDKey(
					node  = servicer.node,
					idkey = servicer.node.id
				))

				# servicer.AddNode(node_list.responding_node)
				servicer.AddNode(node_list.responding_node)

				# add k closest nodes (node_list) to this clients k_buckets
				for node in node_list.nodes:
					servicer.AddNode(node)

				print(f'After BOOTSTRAP({node_list.responding_node.id}), k-buckets are:')
				servicer.PrintKBuckets()

		# command: FIND_NODE <node_id>
		elif cmd == 'FIND_NODE':

			# validate usage
			if len(line) != 1:
				print('Usage: FIND_NODE <node_id>')
				continue

			node_id = line.pop()

			print('Before FIND_NODE command, k-buckets are:')
			servicer.PrintKBuckets()

			# skip to output if local node_id matches requested node_id
			# ( acts as if it found a node )
			if node_id != servicer.node.id:
				pass
			contactedNodes = []
			found = False

			S = servicer.Get_k_closest(node_id)
			for node in S:
				if node.id == node_id:
					found = True
					break
				if node in contactedNodes:
					continue
				else:
					contactedNodes.append(node)
					# R = node.FindNode(node_id)
					servicer.makeNodeMostRecent(node)

					with grpc.insecure_channel(f'{node.address}:{str(node.port)}') as channel:
						stub = pb2_grpc.KadImplStub(channel)

						node_list = stub.FindNode(pb2.IDKey(
							node  = servicer.node,
							idkey = int(node_id)
						))

						for n in node_list.nodes:
							if n.id == node_id:
								found = True
								break
							if servicer.SearchBuckets(n)==False:
								servicer.makeNodeMostRecent(n)

			if not found:
				print(f'Could not find destination id {node_id}')
			else:
				print(f'Found destination id {node_id}')

			print('After FIND_NODE command, k-buckets are:')
			servicer.PrintKBuckets()

		# command: FIND_VALUE <key>
		elif cmd == 'FIND_VALUE':

			# validate usage
			if len(line) != 1:
				print('Usage: FIND_VALUE <key>')
				continue

			key = line.pop()

			print('Before FIND_VALUE command, k-buckets are:')
			servicer.PrintKBuckets()

			# If the target key was found at another node, the program should then print:
			# Found value "<value>" for key <key>
			# If the target key was already stored on the current node, the program should instead print:
			# Found data "<value>" for key <key>
			# Otherwise the program should print:
			# Could not find key <key>
			closest = []

			if servicer.hash_table.get(key)!=None:
				value = servicer.hash_table.get(key)
				print(f'Found data "{value}" for key {key}')
			else:
				# firsk = list()
				contactedNodes = []
				found = False

				nodes = servicer.Get_k_closest_value(key)

				while not found and len(nodes) > 0:
					node = nodes.pop(0)
					if node in contactedNodes:
						continue
					else:
						contactedNodes.append(node)
						servicer.AddNode(node) # update k_buckets
						# closest.append(node)
						# returns list of [<dist,node>,<dist,node>....]
						# R = node[1].FindValue(key)
						# servicer.makeNodeMostRecent(node[1])

						with grpc.insecure_channel(f'{node.address}:{str(node.port)}') as channel:
							stub = pb2_grpc.KadImplStub(channel)

							kv_node_wrapper = stub.FindValue(pb2.IDKey(
								node  = servicer.node,
								idkey = int(key)
							))

							# remote node has been told to store key before
							# get key value
							if kv_node_wrapper.mode_kv:
								print(f'Found value "{kv_node_wrapper.kv.value}" for key {kv_node_wrapper.kv.key}')
								found = True
							# remote node has not been told to store key before
							# get node list
							else:
								nodes += list(kv_node_wrapper.nodes)
								for R_node in kv_node_wrapper.nodes:
										if servicer.SearchBuckets(R_node)[0] == False:
											servicer.makeNodeMostRecent(R_node)

					# if not found:
					# 	#return k closest nodes
					# 	closest.sort()
					# 	if len(closest)>=servicer.k:
					# 		closest = closest[:servicer.k]
			if not found:
				print(f'Could not find key {key}')

			print('After FIND_VALUE command, k-buckets are:')
			servicer.PrintKBuckets()

		# command: STORE <key> <value>
		# The node should send a Store RPC to the single node that has ID closest to the key
		# the current node may be the closest node and may need to store the key/value pair locally
		elif cmd == 'STORE':

			# validate usage
			if len(line) != 2:
				print('Usage: STORE <key> <value>')
				continue

			value = line.pop()
			key   = int(line.pop())

			# find closest node to key
			closest_node = servicer.node
			dist         = closest_node.id ^ key
			for bucket in servicer.k_buckets:
				for node in bucket:
					temp_dist = node.id ^ key
					if temp_dist < dist:
						dist = temp_dist
						closest_node = node

			# store locally
			if closest_node == servicer.node:
				servicer.Store(pb2.KeyValue(
							node  = servicer.node,
							key   = key,
							value = value
				), None)
			# remote storage
			else:
				with grpc.insecure_channel(f'{closest_node.address}:{closest_node.port}') as channel:
					stub = pb2_grpc.KadImplStub(channel)
					stub.Store(pb2.KeyValue(
								node  = servicer.node,
								key   = key,
								value = value
					))

			print(f'Storing key {key} at node {closest_node.id}')

		# command: QUIT
		elif cmd == 'QUIT':

			# send a Quit RPC to each node that is in its k-buckets
			for k_bucket in reversed(servicer.k_buckets):

				for node in reversed(k_bucket):
					# let stored node know that this node is quitting
					with grpc.insecure_channel(f'{node.address}:{str(node.port)}') as channel:
						stub = pb2_grpc.KadImplStub(channel)

						print(f'Letting {str(node.id)} know I\'m quitting.')
						stub.Quit(pb2.IDKey(
							node  = servicer.node,
							idkey = servicer.node.id
						))

			print(f'Shut down node {local_id}')
			break

		# command not supported
		else:
			PrintCommandMenu()


if __name__ == '__main__':
	run()
