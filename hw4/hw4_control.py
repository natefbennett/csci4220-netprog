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