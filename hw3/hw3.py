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

import csci4220_hw3_pb2      as pb2
import csci4220_hw3_pb2_grpc as pb2_grpc

class KadImplServicer(pb2_grpc.KadImplServicer):
	"""Provides methods that implement functionality of a simple Kademlia server."""

	# Member Variables
	n = -1
	k = -1
	node = None  # this servers node info
	k_buckets  = []
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

		# print oldest to newest
		k_buckets = reversed(self.k_buckets)

		# loop through each k bucket and print its nodes
		for i, k_bucket in enumerate(k_buckets):
			line = f'{i}:'
			for node in k_bucket:
				line += f' {node.id}:{node.port}'

			print(line)

	# adds the provided node to a k bucket 
	def AddNode(self, node):
		pass

	# ------------------------------------------- #
	#  Remote Procedure Call (RPC) Methods Below  #
	# ------------------------------------------- #
		
	# RPC: FindNode(IDKey) returns (NodeList)
	def FindNode(self, request, context):
		# return the k closest nodes to the provided ID
		# may need to look in several k-buckets
		# update k-buckets by adding the requester’s ID to be the most recently used
		print('Serving FindNode(<targetID>) request for <requesterID>')
		pass
	
	# RPC: FindValue(IDKey) returns (KV_Node_Wrapper)
	def FindValue(self, request, context):
		# If the remote node has not been told to store the key, 
		# it will reply with the k closest nodes to the key.

		# If the remote node has been told to store the key 
		# before it responds with the key and the associated value.

		print('Serving FindKey(<key>) request for <requesterID>')
		pass
	
	# RPC: Store(KeyValue) returns (IDKey)
	def Store(self, request, context):
		# node receiving the call should 
		# locally store the key/value pair. It should also update 
		# its own k-buckets by adding/updating the requester’s ID 
		# to be the most recently used
		print('Storing key <key> value "<value>"')
		pass

	# RPC: Quit(IDKey) returns (IDKey)
	def Quit(self, request, context):
		# If a node receives a call to Quit from <remoteID>, and the remote node is in k-bucket , the entry should be
		# removed from the k-bucket and the following printed:
		# print('Evicting quitting node <remoteID> from bucket <i>')
		# Otherwise the node should print the following:
		# print('No record of quitting node <remoteID> in k-buckets.')
		pass


# start up simple Kademlia server
def Serve( port, n, k, id ):
	hostname = socket.gethostname() # gets this machine's host name
	ip_addr  = socket.gethostbyname(hostname) # IP address from this hostname

	server   = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
	servicer = KadImplServicer(n, k, id, ip_addr, port)

	pb2_grpc.add_KadImplServicer_to_server( servicer, server)
	server.add_insecure_port(f'[::]:{port}')
	server.start()
	#server.wait_for_termination()

	return servicer

def run():
	if len(sys.argv) != 4:
		print("Error, correct usage is {} [my id] [my port] [k]".format(sys.argv[0]))
		sys.exit(-1)

	local_id = int(sys.argv[1])
	port     = str(int(sys.argv[2])) # add_insecure_port() will want a string
	k        = int(sys.argv[3])
	n        = 4

	# setup server, runs in background
	# returns an instance of KadImplServicer
	servicer = Serve( port, n, k, local_id )

	''' Use the following code to convert a hostname to an IP and start a channel
	Note that every stub needs a channel attached to it
	When you are done with a channel you should call .close() on the channel.
	Submitty may kill your program if you have too many file descriptors open
	at the same time. '''
	
	# remote_addr = socket.gethostbyname(remote_addr_string)
	# remote_port = int(remote_port_string)
	# channel     = grpc.insecure_channel(remote_addr + ':' + str(remote_port))

	# read form stdin for commands
	for line in sys.stdin:
		line = line.split()
		cmd  = line.pop(0)
		
		# command: BOOTSTRAP <remote_hostname> <remote_port>
		if cmd == 'BOOTSTRAP':

			# validate usage
			if len(line) != 2:
				print('Usage: BOOTSTRAP <remote hostname> <remote port>')
				continue

			remote_hostname, remote_port = line

			# TODO: send remote node a FindNode RPC using local node_id
			
			print('After BOOTSTRAP(<remoteID>), k-buckets are:')
			servicer.PrintKBuckets() # TODO: make PrintKBuckets() method

			# TODO: add nodes to k-buckets

		# command: FIND_NODE <node_id>
		elif cmd == 'FIND_NODE':

			# validate usage
			if len(line) != 1:
				print('Usage: FIND_NODE <node_id>')
				continue

			node_id = line.pop()

			print('Before FIND_NODE command, k-buckets are:')
			servicer.PrintKBuckets() # TODO: make PrintKBuckets() method
			
			# skip to output if local node_id matches requested node_id
			# ( acts as if it found a node )
			if node_id != servicer.node_id:
				pass
			#   - Search Algorithm -
			#	While some of the k closest nodes to <nodeID> have not been asked:
			#		S = the k closest IDs to <nodeID>
			#		S' = nodes in S that have not been contacted yet
			#		For node in S':
			#			R = node.FindNode(<nodeID>)
			#			
			# 			# Always mark node as most recently used
			#			Update k-buckets with node
			#			
			# 			# If a node in R was already in a k-bucket, its position does not change.
			#			# If it was not in the bucket yet, then it is added as the most recently used in that bucket.
			#			# This _may_ kick out the node from above.
			#			Update k-buckets with all nodes in R
			#		If <nodeID> has been found, stop

			print('Serving FindNode(<targetID>) request for <requesterID>')
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


			print('After FIND_VALUE command, k-buckets are:')
			servicer.PrintKBuckets()

		# command: STORE <key> <value>
		elif cmd == 'STORE':

			# validate usage
			if len(line) != 2:
				print('Usage: STORE <key> <value>')
				continue

			key, value = line

			# The node should send a Store RPC to the single node that has ID closest to the key
			# the current node may be the closest node and may need to store the key/value pair locally
			print('Storing key <key> at node <remoteID>')

		# command: QUIT
		elif cmd == 'QUIT':
			print('Letting <remoteID> know I\'m quitting.')
			# send a Quit RPC to each node that is in its k-buckets
			print('Shut down node <ID>')
			break

		# command not supported
		else:
			print(
				'Available Commands:\n'                          + \
				'\tBOOTSTRAP  <remote_hostname> <remote_port>\n' + \
				'\tFIND_NODE  <node_id>\n'                       + \
				'\tFIND_VALUE <key>\n'                           + \
				'\tSTORE      <key> <value>\n'                   + \
				'\tQUIT\n'
			)

	# example below from lab5-
	# stub = pb2_grpc.RouteGuideStub(channel)
	# print("-------------- GetFeature --------------")
	# guide_get_feature(stub)
	# print("-------------- ListFeatures --------------")
	# guide_list_features(stub)
	# print("-------------- RecordRoute --------------")
	# guide_record_route(stub)
	# print("-------------- RouteChat --------------")
	# guide_route_chat(stub)
	# print("-------------- RouteRetrieve --------------")
	# guide_route_retrieve(stub) # run tests on RouteRetrieve

if __name__ == '__main__':
	run()
