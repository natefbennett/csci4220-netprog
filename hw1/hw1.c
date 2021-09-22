//
//  main.c
//  hw1
//
//  Created by Anisha Halwai and Nate Bennett on 20/09/21.
//  Copyright Â© 2021 Anisha Halwai. All rights reserved.
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../unpv13e/lib/unp.h"

#define MAX_DATA_SIZE 512
#define ABORT_TIMEOUT 10
#define RETRANSMIT_TIMEOUT 1

#define MAX_PORT 49151
#define MIN_PORT 1024

/*
 1     Read request (RRQ)
 2     Write request (WRQ)
 3     Data (DATA)
 4     Acknowledgment (ACK)
 5     Error (ERROR)
*/
enum opcode{ RRQ=1, WRQ=2, DATA=3, ACK=4, ERROR=5 };

/*	2 bytes     string      1 byte     string   1 byte
	----------------------------------------------------
   | Opcode=1/2 |  Filename  |   0  | Mode==octet |  0  |	RRQ/WRQ packet
	---------------------------------------------------- 			    */
typedef struct {
	int opcode;
	char filename[MAX_DATA_SIZE];
} rw_request;


/*  2 bytes     2 bytes      n bytes
	----------------------------------
   | Opcode=3 |   Block #  |   Data   |	  DATA packet
	----------------------------------		   	   */
typedef struct {
	int opcode;
	int blocknum;
    int data[MAX_DATA_SIZE];
} data_packet;

/* 	  2 bytes     2 bytes
	 ---------------------
	| Opcode=4 |  Block # |		ACK packet
	 ---------------------				*/
typedef struct {
	int opcode;
	int blocknum;
} ack_packet;

/* 2 bytes     2 bytes      string    1 byte
  -------------------------------------------
 | Opcode=5 |  ErrorCode |   ErrMsg   |   0  |		ERROR packet
  -------------------------------------------   			  */
typedef struct {
	int opcode;
	int errorcode;
	char errorstring[MAX_DATA_SIZE];
} error_packet;

// send ACK packet
void SendAck()
{

}

// send DATA packet
void SendData()
{

}

// send ERROR packet
void SendError()
{

}

// recieve read/write request
void RecvReadWrite()
{

}

// signal handler
void SigHandler()
{
    int stat;
    waitpid(-1, &stat, WNOHANG);
}

int main (int argc, char *argv[])
{
    // NOTE: for Submitty (auto-grader) use only
    setvbuf( stdout, NULL, _IONBF, 0 ); 
    
    // check number of command line args
    if ( argc != 3 )
    {
        fprintf(stderr, "Error: Incorrect usage\n<%s> [start of port range] [end of port range]\n", argv[0]);
        return EXIT_FAILURE;
    }

    // check if port range correct
    int start_port = atoi(argv[1]);
    int end_port = atoi(argv[2]);
    int next_port = start_port++;    // set up port for forked process

    if ( start_port < MIN_PORT   || 
         end_port   < start_port || 
         end_port   > MAX_PORT ) 
    {
        fprintf(stderr, "Error: Invalid port number: Must be in range [%d, %d]\n", MIN_PORT, MAX_PORT);
        return EXIT_FAILURE;        
    }

    // create a socket and bind to it
	int					sockfd;
	struct sockaddr_in	servaddr, cliaddr;

	sockfd = Socket(AF_INET, SOCK_DGRAM, 0);

	bzero(&servaddr, sizeof(servaddr));
	servaddr.sin_family      = AF_INET;
	servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
	servaddr.sin_port        = htons(start_port);

	Bind(sockfd, (SA *) &servaddr, sizeof(servaddr));

    // setup signal handler
    Signal(SIGCHLD, SigHandler);

    int         n;    // response length
    char        msg;  // data recieved from a client
    socklen_t   len;

    // infinite loop for server
    for ( ; ; )
    {
        len = sizeof(cliaddr);
        n = Recvfrom( sockfd, &msg, MAX_DATA_SIZE, 0, (SA *) &cliaddr, &len );

        // handle incorrect message lengths??

        // get opcode from message
        short raw_opcode;
        memcpy(&raw_opcode, msg, sizeof(raw_opcode));
        short opcode = ntohs(raw_opcode);

        // handle new read or write request, other packet types are handled in child fork
        if ( opcode == WRQ || opcode == RRQ )
        {
            RecvReadWrite( &msg, len, &cliaddr, next_port );
            next_port++;
        }
    }

    
    return EXIT_SUCCESS;
}

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
