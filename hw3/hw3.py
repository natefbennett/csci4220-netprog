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
            id=id,
            port=int(port),
            address=addr
        )

    def PrintKBuckets(self):

        # loop through each k bucket and print its nodes
        # print oldest to newest
        for i, k_bucket in enumerate(self.k_buckets):
            line = f'{i}:'
            for node in reversed(k_bucket):
                line += f' {node.id}:{node.port}'

            print(line)

    # adds the provided node to a k bucket
    def AddNode(self, node):
        dist = distance(node,self.node)

        # check [i,N) k-buckets
        for i in range(self.n):
            lowerbound = 2**i
            upperbound = 2**(i+1)
            if lowerbound<dist and dist<=upperbound:
                self.k_buckets[i].append(node)
                return 0

        #Error handling: failure to add node to a k-bucket
        return -1

    def DeleteNode(self,node):
        dist = distance(node, self.node)

        # check [i,N) k-buckets
        for i in range(self.n):
            lowerbound = 2 ** i
            upperbound = 2 ** (i + 1)
            if lowerbound < dist and dist <= upperbound:
                index = self.k_buckets[i].index(node)
                deletedNode = self.k_buckets[i].pop(index)

                # Error handling: if deleted node is not the node given
                if deletedNode!=node:
                    return -1

                return 0

        # Error handling: failure to delete node to a k-bucket
        return -1

    # ------------------------------------------- #
    #  Remote Procedure Call (RPC) Methods Below  #
    # ------------------------------------------- #

    # RPC: FindNode(IDKey) returns (NodeList)
    def FindNode(self, request, context):
        # return the k closest nodes to the provided ID
        # may need to look in several k-buckets

        found=0
        allNodes = list()
        while found<self.k:
            continue

        # update k-buckets by adding the requester’s ID to be the most recently used
        # remove node id from i'th k-bucket, appending node id again(change
        # position to be last/most recently used node id)
        # [<older entry>, <next oldest>, ... ,<newest entry>]

        self.DeleteNode(request.node)
        self.AddNode(request.node)

        print(
            f'Serving FindNode({request.idkey}) request for {request.node.id}')
        pass

    # RPC: FindValue(IDKey) returns (KV_Node_Wrapper)
    def FindValue(self, request, context):
        # If the remote node has not been told to store the key,
        # it will reply with the k closest nodes to the key.

        # If the remote node has been told to store the key
        # before it responds with the key and the associated value.

        print(
            f'Serving FindKey({request.idkey}) request for {request.node.id}')

    # RPC: Store(KeyValue) returns (IDKey)
    # warining: does not check for collisions
    def Store(self, request, context):

        print(f'Storing key {request.key} value "{request.value}"')
        self.hash_table[request.key] = request.value

        # TODO: update k_buckets, add requester's ID to be most recently used

        # returns the node that the key value pair was stored and the key
        return pb2.IDKey(
            node=self.node,
            idkey=request.key
        )

    # RPC: Quit(IDKey) returns (IDKey)
    def Quit(self, request, context):

        for i, k_bucket in enumerate(self.k_buckets):
            # check k buckets for requested node
            if request.node in k_bucket:
                print(
                    f'Evicting quitting node {request.node.id} from bucket {i}')
                k_bucket.remove(request.node)

                return pb2.IDKey(
                    node=self.node,
                    idkey=request.node.id
                )

        # node not found
        print(f'No record of quitting node {request.node.id} in k-buckets.')
        return None

# passing in 2 binary representations of nodeA and nodeB
def distance(nodeA, nodeB):
    return nodeA^nodeB

# start up simple Kademlia server
def Serve(port, n, k, id):
    hostname = socket.gethostname()  # gets this machine's host name
    ip_addr = socket.gethostbyname(hostname)  # IP address from this hostname

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = KadImplServicer(n, k, id, ip_addr, port)

    pb2_grpc.add_KadImplServicer_to_server(servicer, server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    # server.wait_for_termination()

    return servicer


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
    servicer = Serve(port, n, k, local_id)

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
        cmd = line.pop(0)

        # command: BOOTSTRAP <remote_hostname> <remote_port>
        if cmd == 'BOOTSTRAP':

            # validate usage
            if len(line) != 2:
                print('Usage: BOOTSTRAP <remote hostname> <remote port>')
                continue

            remote_hostname, remote_port = line

            # TODO: send remote node a FindNode RPC using local node_id

            print('After BOOTSTRAP(<remoteID>), k-buckets are:')
            servicer.PrintKBuckets()  # TODO: make PrintKBuckets() method

        # TODO: add nodes to k-buckets

        # command: FIND_NODE <node_id>
        elif cmd == 'FIND_NODE':

            # validate usage
            if len(line) != 1:
                print('Usage: FIND_NODE <node_id>')
                continue

            node_id = line.pop()

            print('Before FIND_NODE command, k-buckets are:')
            servicer.PrintKBuckets()  # TODO: make PrintKBuckets() method

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

            int(key), value = line

            # The node should send a Store RPC to the single node that has ID closest to the key
            # the current node may be the closest node and may need to store the key/value pair locally
            print(f'Storing key {key} at node <remoteID>')

        # command: QUIT
        elif cmd == 'QUIT':

            # send a Quit RPC to each node that is in its k-buckets
            for k_bucket in reversed(servicer.k_buckets):
                for node in reversed(k_bucket):
                    # let stored node know that this node is quitting
                    with grpc.insecure_channel(
                            f'{node.address}:{str(node.port)}') as channel:
                        stub = pb2_grpc.KadImplStub(channel)

                        print(f'Letting {str(node.id)} know I\'m quitting.')
                        stub.Quit(pb2.IDKey(
                            node=servicer.node,
                            idkey=servicer.node.id
                        ))

            print(f'Shut down node {local_id}')
            break

        # command not supported
        else:
            print(
                'Available Commands:\n' + \
                '\tBOOTSTRAP  <remote_hostname> <remote_port>\n' + \
                '\tFIND_NODE  <node_id>\n' + \
                '\tFIND_VALUE <key>\n' + \
                '\tSTORE      <key> <value>\n' + \
                '\tQUIT\n'
            )


if __name__ == '__main__':
    run()