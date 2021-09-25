     
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
//#include "../unpv13e/lib/unp.h"
#include "unp.h" // for submitty

#define MAX_DATA_SIZE       512
#define MAX_PACKET_LEN      516
#define MIN_PACKET_LEN      4
#define ABORT_TIMEOUT       10
#define RETRANSMIT_TIMEOUT  1

#define MAX_PORT 49151
#define MIN_PORT 1024

typedef unsigned char byte;

// define error messages
char *errorcode[] = 
{
    "Not defined, see error message (if any).",   // [0]
    "File not found.",                            // [1]
    "Access violation.",                          // [2]
    "Disk full or allocation exceeded",           // [3]
    "Illegal TFTP operation.",                    // [4]
    "Unknown transfer ID.",                       // [5]
    "File already exists",                        // [6]
    "No such user."                               // [7]
};

/*
 1     Read request (RRQ)
 2     Write request (WRQ)
 3     Data (DATA)
 4     Acknowledgment (ACK)
 5     Error (ERROR)
*/
enum opcode { RRQ=1, WRQ=2, DATA=3, ACK=4, ERROR=5 };

typedef union {

	/*	2 bytes     string      1 byte     string   1 byte
		----------------------------------------------------
	   | Opcode=1/2 |  Filename  |   0  | Mode==octet |  0  |	RRQ/WRQ packet
		---------------------------------------------------- 			    */
	struct {
		short opcode;
		char filename[MAX_DATA_SIZE+2];
	} rw_request;

	/*  2 bytes     2 bytes      n bytes
		----------------------------------
	   | Opcode=3 |   Block #  |   Data   |	  DATA packet
		----------------------------------		   	   */
	struct {
		short opcode;
		short blocknum;
		byte data[MAX_DATA_SIZE];
	} data_packet;

	/* 	  2 bytes     2 bytes
		 ---------------------
		| Opcode=4 |  Block # |		ACK packet
		 ---------------------				*/
	struct {
		short opcode;
		short blocknum;
	} ack_packet;

	/* 2 bytes     2 bytes      string    1 byte
	  -------------------------------------------
	 | Opcode=5 |  ErrorCode |   ErrMsg   |   0  |		ERROR packet
	  -------------------------------------------   			  */
	struct {
		short opcode;
		short errorcode;
		char errorstring[MAX_DATA_SIZE];
	} error_packet;
	
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
void SendAck(short blocknum, int sockfd, struct sockaddr_in *sock_inf,
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
	printf("Sending ACK (blocknum: %d)\n", blocknum);
}

// send DATA packet
void SendData(short blocknum, int sockfd, struct sockaddr_in *sock_inf,
			socklen_t socklen, size_t chunk_len, byte data_from_datapacket[MAX_DATA_SIZE])
{
	
	packet pack;
	pack.data_packet.opcode = htons(DATA);
	pack.data_packet.blocknum = htons(blocknum);
	memcpy(pack.data_packet.data, data_from_datapacket, chunk_len);
	
    int len_with_header = chunk_len+4;
	ssize_t sent = sendto(sockfd, &pack, len_with_header,0,
				(struct sockaddr *) sock_inf,socklen);
				
	if(sent<0){
		perror("send to failed\n");
		exit(1);
	}
    printf("Sending DATA (blocknum: %d, len: %zu)\n", blocknum, chunk_len);
}

// send ERROR packet
void SendError(short errorcode, int sockfd, struct sockaddr_in *sock_inf,
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
    printf("Sending ERROR (error code: %d)\nError Message: %s\n", errorcode, error_msg);
}

// recieve read/write request
void RecvReadWrite(short opcode, packet *msg, socklen_t len, struct sockaddr_in *cliaddr, int next_port)
{
    // open new port and bind to socket
	int					sockfd;
	struct sockaddr_in	servaddr;
    int                 recv_size; // eturn from Recvfrom()

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
        if( fork() == 0 ) // child
        {
			// check to make sure in octet mode
            char *file = msg->rw_request.filename;
            char *filemode = strchr(file,'\0')+1;

            if( strcasecmp(filemode, "octet") != 0 )
            {
                perror("Invalid octet file mode\n");
                exit(1);
            }

            // open file for reading binary
			FILE *fd = fopen(file,"rb");
			if( fd == NULL )
			{
				perror("file couldn't be opened\n");
				SendError(errno, sockfd, cliaddr, sizeof(*cliaddr), errorcode[1]);
				exit(1);
			}

            printf("Handeling read request of file: %s\n",file);
        
			// track block number and send acknowledgement
			short blocknum = 1;
		
			// loop till all datagrams sent (data packet with less the 512 bytes of data)
			bool thats_everything = false;
			while( !thats_everything )
            {
                // variables for storing read data
                byte data_chunk[MAX_DATA_SIZE];
                size_t chunk_len;

                // read in data from file
                chunk_len = fread(data_chunk, 1, MAX_DATA_SIZE, fd);

				// attempt to send data and wait for ack
				int attempt = 10;
				while( attempt > 0 )
				{
                    SendData(blocknum, sockfd, cliaddr, len, chunk_len, data_chunk);
				    alarm(RETRANSMIT_TIMEOUT); // set an alarm
					recv_size = Recvfrom(sockfd, msg, sizeof(*msg), 0, (struct sockaddr *)cliaddr, &len);
					                
					if( recv_size < 0 )
                    {
                        // check for timeout
                        if ( errno == EINTR )
                        {
                            printf("Server socket timeout");
                        }
						perror("recvfrom failed\n");
					}
					
					//check if any data recvd --> rev>4 since opcode+blocknum = 2+2
					if( recv_size >= MIN_PACKET_LEN )
                    {
                        alarm(0); // cancel alarm, data recieved
						attempt = -1; // end loop
					}
					
                    // resend ack packet if can make more attempts
					if( attempt != -1 )
                    {
						SendAck(blocknum, sockfd, cliaddr, sizeof(*cliaddr));
					}

					attempt--;
				}
				
				if( attempt == 0 ){
					printf("Transfer timed out, abort connection\n");
					exit(1);
				}

                // get opcode from message
                short raw_opcode;
                memcpy(&raw_opcode, msg, sizeof(raw_opcode));
                opcode = ntohs(raw_opcode);

                // data left to send less than 512 bytes
				if( chunk_len < MAX_DATA_SIZE )
				{
					thats_everything = true;
				}
                
				// check for acknowledgement
                if ( opcode == ACK )
                {
                    printf("Received ACK (blocknum: %d)\n", blocknum);
                 
                    // validate block number
                    if ( htons(blocknum) != msg->ack_packet.blocknum )
                    {
                        printf("Error wrong block recieved (blocknum: %d)\n",ntohs(msg->ack_packet.blocknum));
                        SendError(errno, sockfd, cliaddr, sizeof(*cliaddr), "Server recieved wrong block number");
                        exit(1);
                    }
                }
                // got error message
                else if ( opcode == ERROR )
                {
                    printf("Recieved error from connected client!\n+>Error: %s", msg->error_packet.errorstring);
                    exit(1);
                }
                // was expecting an ACK or Error, fail
                else
                {
                    SendError(errno, sockfd, cliaddr, sizeof(*cliaddr), strerror(errno));
                }
                blocknum++;
			}
			
            fclose(fd);
            close(sockfd);
            printf("Completed RRQ\n");
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
			// int sockend = Socket(AF_INET, SOCK_DGRAM, 0);
			// if(sockend==-1){
			// 	perror("socket failed.\n");
			// 	exit(1);
			// }
			//then open file

			FILE *fd = fopen(file,"w");
			if(fd == NULL)
			{
				perror("file couldn't be opened");
				SendError(errno, sockfd, cliaddr, sizeof(*cliaddr), strerror(errno));
				exit(1);
			}

            printf("Handeling write request of file: %s\n",file);

			//send ack 0 packet
			short blocknum = 0;
			SendAck(blocknum, sockfd, cliaddr, len);
		
			//loop till all datagrams receieved
			bool thats_everything = false;
			while(!thats_everything){
				//loop till datagram recved (resending lost datagrams, ? number of time)
				int attempt=10;
				while(attempt>0)
				{
				    socklen_t lenn = sizeof(cliaddr);
					recv_size = Recvfrom(sockfd, msg, sizeof(*msg), 0, (struct sockaddr *)cliaddr, &lenn);
					
					if(recv_size<0){
						perror("recvfrom failed\n");
					}
					
					//check if any data recvd --> rev>4 since opcode+blocknum = 2+2
					if( recv_size >= MIN_PACKET_LEN ){
						//end loop
						attempt = -1;
					}
					
					if(attempt!=-1){
						//data packet not received correctly
						//resend ack packet
						SendAck(blocknum, sockfd, cliaddr, sizeof(*cliaddr));
					}
					attempt--;
				}
				
				if(attempt==0){
					printf("Transfer timed out, abort connection");
					exit(1);
				}
				//error handling
				blocknum++;
				
				if(MAX_DATA_SIZE > recv_size)
				{
					thats_everything = true;
				}
				//write contents in file
				msg->data_packet.data[512] = '\0';
				int written = fwrite(msg->data_packet.data, 1,recv_size-4,fd );
				if(written < 0)
				{
					perror("fwrite failed\n");
					exit(1);
				}
				
				//send ack for block 1
				SendAck(blocknum, sockfd, cliaddr, sizeof(*cliaddr));
				
			}
			
            fclose(fd);
            close(sockfd);
            printf("Completed WRQ\n");
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

    int         recv_size;    // Recvfrom() response
    socklen_t   len;
    int next_port = start_port+1;

    // infinite loop for server
    for ( ; ; )
    {
		packet msg;
        len = sizeof(cliaddr);
        recv_size = Recvfrom( sockfd, &msg, sizeof(msg), 0, (SA *) &cliaddr, &len );

        // handle incorrect message lengths
        if ( recv_size < MIN_PACKET_LEN )
        {
            //TODO: send error
            printf("Packe recieved too small: %d bytes", recv_size);
            continue;
        }
        else if ( recv_size > MAX_PACKET_LEN )
        {
            //TODO: send error
            printf("Packe recieved too big: %d bytes", recv_size);
            continue;
        }
        else if ( recv_size < 0  )
        {
            perror("Recvfrom() failed");
            continue;
        }


        // get opcode from message
        short raw_opcode;
        memcpy(&raw_opcode, &msg, sizeof(raw_opcode));
        short opcode = ntohs(raw_opcode);

        // handle new read or write request, other packet types are handled in child fork
        if ( opcode == WRQ || opcode == RRQ )
        {
            printf("Current TID: %d\n", next_port-1);
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

