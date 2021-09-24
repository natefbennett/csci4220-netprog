     
//
//  main.c
//  hw1
//
//  Created by Anisha Halwai and Nate Bennett on 20/09/21.
//  Copyright Â© 2021 Anisha Halwai. All rights reserved.
//

#include <netdb.h>
#include <unistd.h>
#include <strings.h>
#include <string.h>
#include <signal.h>
#include <stdbool.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <stdio.h>
#include <stdlib.h>
#include "../../unpv13e/lib/unp.h"

#define MAX_DATA_SIZE       512
#define MAX_MSG_SIZE        516
#define ABORT_TIMEOUT       10
#define RETRANSMIT_TIMEOUT  1

#define MAX_PORT 49151
#define MIN_PORT 1024

typedef unsigned char byte;

/*
 1     Read request (RRQ)
 2     Write request (WRQ)
 3     Data (DATA)
 4     Acknowledgment (ACK)
 5     Error (ERROR)
*/
enum opcode{ RRQ=1, WRQ=2, DATA=3, ACK=4, ERROR=5 };

typedef union{

	/*	2 bytes     string      1 byte     string   1 byte
		----------------------------------------------------
	   | Opcode=1/2 |  Filename  |   0  | Mode==octet |  0  |	RRQ/WRQ packet
		---------------------------------------------------- 			    */
	struct{
		int opcode;
		char filename[MAX_DATA_SIZE+2];
	}rw_request;

	/*  2 bytes     2 bytes      n bytes
		----------------------------------
	   | Opcode=3 |   Block #  |   Data   |	  DATA packet
		----------------------------------		   	   */
	struct {
		int opcode;
		int blocknum;
		int data[MAX_DATA_SIZE];
	} data_packet;

	/* 	  2 bytes     2 bytes
		 ---------------------
		| Opcode=4 |  Block # |		ACK packet
		 ---------------------				*/
	struct{
		int opcode;
		int blocknum;
	} ack_packet;

	/* 2 bytes     2 bytes      string    1 byte
	  -------------------------------------------
	 | Opcode=5 |  ErrorCode |   ErrMsg   |   0  |		ERROR packet
	  -------------------------------------------   			  */
	struct{
		int opcode;
		int errorcode;
		char errorstring[MAX_DATA_SIZE];
	}error_packet;
	
} packet;

// child termination signal handler
void SigChildHandler()
{
    int stat;
    waitpid(-1, &stat, WNOHANG);
}

// timeout alarm signal handler
void SigAlarmHandler()
{
    return; // just interrupt the recvfrom()
}

// send ACK packet
void SendAck(int blocknum, int sockfd, struct sockaddr_in *sock_inf,
			socklen_t socklen)
{
	packet pack;
	pack.ack_packet.opcode = htons(ACK);
	pack.ack_packet.blocknum = htons(blocknum);
	
	ssize_t sent = sendto(sockfd, &pack, sizeof(pack),0,
				(struct sockaddr *) sock_inf,socklen);
				
	if(sent<0){
		perror("send to failed\n");
		exit(1);
	}
	
}

// send DATA packet
void SendData(int blocknum, int sockfd, struct sockaddr_in *sock_inf,
			socklen_t socklen, char data_from_datapacket[MAX_DATA_SIZE])
{
	
	packet pack;
	pack.data_packet.opcode = htons(DATA);
	pack.data_packet.blocknum = htons(blocknum);
	memcpy(pack.data_packet.data, data_from_datapacket, MAX_DATA_SIZE);
	
	ssize_t sent = sendto(sockfd, &pack, sizeof(pack),0,
				(struct sockaddr *) sock_inf,socklen);
				
	if(sent<0){
		perror("send to failed\n");
		exit(1);
	}

}

// send ERROR packet
void SendError(int errorcode, int sockfd, struct sockaddr_in *sock_inf,
			socklen_t socklen, char error_msg[MAX_DATA_SIZE])
{

	packet pack;
	pack.error_packet.opcode = htons(ERROR);
	pack.error_packet.errorcode = errorcode;
	memcpy(pack.error_packet.errorstring, error_msg, MAX_DATA_SIZE);
	
	ssize_t sent = sendto(sockfd, &pack, sizeof(pack),0,
				(struct sockaddr *) sock_inf,socklen);
				
	if(sent<0){
		perror("send to failed\n");
		exit(1);
	}

}

// recieve read/write request
void RecvReadWrite(short opcode, packet *msg, socklen_t len, struct sockaddr_in *cliaddr, int next_port)
{
    // open new port and bind to socket
	int					sockfd;
	struct sockaddr_in	servaddr;
    int                 n;    // recvfrom() response length

	sockfd = Socket(AF_INET, SOCK_DGRAM, 0);

	bzero(&servaddr, sizeof(servaddr));
	servaddr.sin_family      = AF_INET;
	servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
	servaddr.sin_port        = htons(next_port);

	Bind(sockfd, (SA *) &servaddr, sizeof(servaddr));
    
    // register timeout alarm
    Signal(SIGALRM, SigAlarmHandler);

    if ( opcode == RRQ )
    {
        // TODO: cast msg to read_request struct
        struct rw_request r_req;
        memcpy( &r_req, msg, sizeof(r_req) );
        char *filename = r_req.filename;

        if( fork() == 0 ) // child
        {
            // open file
            FILE *fptr;

            if ( (fptr = fopen(filename,"rb")) == NULL ){
                fprintf(stderr, "File does not exist!");
                exit(1);
            }

            int last_dgram = 0;

            // loop while still getting datagrams
            while(!last_dgram)
            {
                byte cur_block[MAX_DATA_SIZE];
                fread(&cur_block, MAX_DATA_SIZE, 1, fptr);
                last_dgram = 1; // terminate for now
                // TODO: create data packet and send data to client
            }
            fclose(fptr);
        }
    }
    else if ( opcode == WRQ )
    {
    
		
        if( fork() == 0 ) // child
        {
			//get file from msg
			char *file = msg->rw_request.filename;
			char *filemode = strchr(file,'\0')+1;
			
			if(strcasecmp(filemode, "octet")!=0){
				perror("Invalid octet file mode\n");
				exit(1);
			}
			
			//create socket endpoint
			int sockend = Socket(AF_INET, SOCK_DGRAM, 0);
			if(sockend==-1){
				perror("socket failed.\n");
				exit(1);
			}
			//then open file
			FILE *fd = fopen(file,"w");
			if(fd == NULL)
			{
				perror("file couldn't be opened");
				SendError(errno, sockend, cliaddr, sizeof(*cliaddr), strerror(errno));
				exit(1);
			}
			//send ack 0 packet
			int blocknum=0;
			SendAck(blocknum, sockend, cliaddr, len);
		
			//loop till all datagrams receieved
			bool thats_everything = false;
			while(!thats_everything){
				//loop till datagram recved (resending lost datagrams, ? number of time)
				int attempt=10;
				while(attempt>0)
				{
				    socklen_t lenn = sizeof(cliaddr);
					ssize_t recv = recvfrom(sockend, msg, sizeof(*msg), 0, (struct sockaddr *)cliaddr, &lenn);
					
					if(recv<0){
						perror("recvfrom failed\n");
					}
					
					//check if any data recvd --> rev>4 since opcode+blocknum = 2+2
					if(recv>=4){
						//end loop
						attempt = -1;
					}
					
					if(attempt!=-1){
						//data packet not received correctly
						//resend ack packet
						SendAck(blocknum, sockend, cliaddr, sizeof(*cliaddr));
					}
					attempt--;
				}
				
				if(attempt==0){
					printf("Transfer timed out, abort connection");
					exit(1);
				}
				//error handling
				blocknum++;
				
				if(sizeof(msg->data_packet) >recv)
				{
					thats_everything = true;
				}
				//write contents in file
				msg->data_packet.data[512] = '\0';
				int written = fwrite(msg->data_packet.data, 1,recv-4,fd );
				if(written < 0)
				{
					perror("fwrite failed\n");
					exit(1);
				}
				
				//send ack for block 1
				SendAck(blocknum, sockend, cliaddr, sizeof(*cliaddr));
				
			}
			
            fclose(fd);
            close(sockend);
        }
        
    }
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
    Signal(SIGCHLD, SigChildHandler);

    int         n;    // recvfrom() response length
//    char        msg;  // data recieved from a client
    socklen_t   len;

    // infinite loop for server
    for ( ; ; )
    {
		packet msg;
        len = sizeof(cliaddr);
        n = Recvfrom( sockfd, &msg, sizeof(msg), 0, (SA *) &cliaddr, &len );

        // handle incorrect message lengths??

        // get opcode from message
        short raw_opcode;
        memcpy(&raw_opcode, &msg, sizeof(raw_opcode));
        short opcode = ntohs(raw_opcode);

        // handle new read or write request, other packet types are handled in child fork
        if ( opcode == WRQ || opcode == RRQ )
        {
            RecvReadWrite( opcode, &msg, len, &cliaddr, next_port );
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

