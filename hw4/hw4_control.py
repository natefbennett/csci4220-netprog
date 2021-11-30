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

def run():
    
    # check number of command line args
    if len(sys.argv) != 4:
        print(f'Usage: python3 -u {sys.argv[0]} [control port] [base station file]')
        sys.exit(-1)

if __name__ == '__main__':
	run()