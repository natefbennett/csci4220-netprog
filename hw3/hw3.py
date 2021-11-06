#!/usr/bin/env python3

from concurrent import futures
import sys  # For sys.argv, sys.exit()
import socket  # for gethostbyname()

import grpc

import csci4220_hw3_pb2      as pb2
import csci4220_hw3_pb2_grpc as pb2_grpc

class SimpleKadServicer(pb2_grpc.SimpleKadServicer):
	"""Provides methods that implement functionality of a simple Kademlia server."""

	def __init__(self):
		pass

	def FindNode(self):
		pass

	def FindValue(self):
		pass
	
	def Store(self):
		pass

	def Quit(self):
		pass

# start up simple Kademlia server
def serve( port ):
	server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
	pb2_grpc.add_SimpleKadServicer_to_server(
		SimpleKadServicer(), server)
	server.add_insecure_port(f'[::]:{port}')
	server.start()
	server.wait_for_termination()
	return server

def run():
	if len(sys.argv) != 4:
		print("Error, correct usage is {} [my id] [my port] [k]".format(sys.argv[0]))
		sys.exit(-1)

	local_id = int(sys.argv[1])
	port     = str(int(sys.argv[2])) # add_insecure_port() will want a string
	k        = int(sys.argv[3])
	n        = 4
	hostname = socket.gethostname() # gets this machine's host name
	address  = socket.gethostbyname(hostname) # IP address from this hostname

	# setup server, runs in background
	server = serve( port )

	''' Use the following code to convert a hostname to an IP and start a channel
	Note that every stub needs a channel attached to it
	When you are done with a channel you should call .close() on the channel.
	Submitty may kill your program if you have too many file descriptors open
	at the same time. '''
	
	remote_addr = socket.gethostbyname(remote_addr_string)
	remote_port = int(remote_port_string)
	channel     = grpc.insecure_channel(remote_addr + ':' + str(remote_port))

	# read form stdin for commands
	# example below from lab5
	'''
	stub = pb2_grpc.RouteGuideStub(channel)
	print("-------------- GetFeature --------------")
	guide_get_feature(stub)
	print("-------------- ListFeatures --------------")
	guide_list_features(stub)
	print("-------------- RecordRoute --------------")
	guide_record_route(stub)
	print("-------------- RouteChat --------------")
	guide_route_chat(stub)
	print("-------------- RouteRetrieve --------------")
	guide_route_retrieve(stub) # run tests on RouteRetrieve
	'''


if __name__ == '__main__':
	run()
