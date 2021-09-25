# TFTP Server

/*	TFTP according to RFC 1350
	only read and write files
	modes of transer: netascii, octet, and mail
	*** to implement: octet
	
	* Protocol: *
	* transfer begins with a request to read or write a file
	* which means a connection is requested
	* if connection granted:
		file sent in blocks of data of 512 bytes.
		data packet of <512 bytes --> termination of a transfer
		if packet gets lost --> no packet received for at least 1 second, packet resent
	* error packet:
		error signalled by sending error packet, leads to termination
		this packet is not acknowledged and not retransmitted (resent on timeout)
		when lost, a timeout will be responsible for transfer termination
		TYPES OF ERRORS: ...
	* Data packets (dont think we need to implement this):
		---------------------------------------------------
		|  Local Medium  |  Internet  |  Datagram  |  TFTP |
		---------------------------------------------------
		Internet header + Datagram header + TFTP header + remainder of TFTP packet (in order)
		0<= TID <= 65,535
		** TFTP header --> 2 bytes opcode (indicates packet type)
		
	
	** 	INITIAL CONNECTION:
	* Transfer established by sending a request -->
		WRQ: write to foreign file system
		RRQ: read from foreign file system
	* ack packet for write, or data packet for read.
	* ACK PACKET --> block number of the data being acked (starting with 1)
					 block number to ack write request = 0
	* Connection: each end of connection should choose a random TID
				  every packet contains the source and destination TID
	
	1. Host A sends  a  "WRQ"  to  host  B  with  source=  A's  TID,
	   destination= 69.
	2. Host  B  sends  a "ACK" (with block number= 0) to host A with
	   source= B's TID, destination= A's TID.
	   
	opcode  operation
	1     Read request (RRQ)
	2     Write request (WRQ)
	3     Data (DATA)
	4     Acknowledgment (ACK)
	5     Error (ERROR)
	
	
	   2 bytes     string      1 byte     string   1 byte
	 ----------------------------------------------------
	| Opcode=1/2 |  Filename  |   0  | Mode==octet |  0  |	RRQ/WRQ packet
	 ----------------------------------------------------
					
					
	 2 bytes     2 bytes      n bytes
	 ----------------------------------
	| Opcode=3 |   Block #  |   Data     |	DATA packet
	 ----------------------------------
					|			|
				1,2,3,...	 0-512 bytes
							if data<512 bytes long, end of transfer after ack
							(normal termination)
				
	 2 bytes     2 bytes
	 ---------------------
	| Opcode=4 |   Block #  |		ACK packet
	 ---------------------
		
	
	  2 bytes     2 bytes      string    1 byte
	 -------------------------------------------
	| Opcode=5 |  ErrorCode |   ErrMsg   |   0  |		ERROR packet
	 -------------------------------------------
	 
	 
	**************************************************
	Hw specific:
	* Use SIGALRM - useful to implement timeouts
	* do not request port 69, instead:
		argv[1] = start of port range
		argv[2] = end of port range
		use first available port in this range
	* TIDs - instead of using random TIDs, use next highest port in the range (next available port?)
		   - do not reuse ports for TIDs
*/
