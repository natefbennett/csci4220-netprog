#include <stdio.h>
#include <stdlib.h>

// adjust lib path if "DEV" compiler macro used 
#ifdef DEV
#include "../unpv13e/lib/unp.h"
#endif

// adjust lib path if "SUBMITTY" compiler macro used 
#ifdef SUBMITTY
#include "unp.h"
#endif

#define START_PORT  9877
#define	MAXLINE		4096

// read in line of input and send to client
// return 1 if client disconnects
// return 0 if reached EOF
int SendInput(FILE *fp, int sockfd)
{
	char	sendline[MAXLINE], recvline[MAXLINE];

	while (Fgets(sendline, MAXLINE, fp) != NULL) {

		Writen(sockfd, sendline, strlen(sendline));

		if (Readline(sockfd, recvline, MAXLINE) == 0)
        {
            printf("str_cli: client disconnected");
            return 1;
        }
		
		Fputs(recvline, stdout);
	}
    return 0;
}

int main ( int argc, char *argv[] )
{
	if (argc != 2)
		err_quit("usage: %s <int>", argv[0]);

    int port = atoi(argv[1]) + START_PORT;

    // set up socket for server and bind to it
    int					listenfd, connfd, sockfd;
    socklen_t			clilen;
	struct sockaddr_in	cliaddr, servaddr;

	listenfd = Socket(AF_INET, SOCK_STREAM, 0);

    // for debug, solves error on binding, already in use
    int optval = 1;
    setsockopt(listenfd, SOL_SOCKET, SO_REUSEADDR, 
            (const void *)&optval , sizeof(int));

    // set server address and port
	bzero(&servaddr, sizeof(servaddr));
	servaddr.sin_family      = AF_INET;
	servaddr.sin_port        = htons(port);
	Inet_pton(AF_INET, "127.0.0.1", &servaddr.sin_addr);

    // bind to port and listen on it
    Bind(listenfd, (SA *) &servaddr, sizeof(servaddr));
    Listen(listenfd, LISTENQ);

    clilen = sizeof(cliaddr);
    int connected = 0;
    int eof = 0;
    while( !eof )
    {
        // if not already connected, accept connection
        if ( !connected ) {
            connfd = Accept(listenfd, (SA *) &cliaddr, &clilen);
            printf(">Accepted connection\n");
            connected = 1;
        }

        // accept input from stdin while connected to client
        while ( connected )
        {
            // read in stdin, send to client
            int disconnected = SendInput(stdin, connfd);

            // client disconnected, accept new connections again
            if ( disconnected ) { connected = 0; }

            // end of file recieved, shut down server
            if ( !disconnected ) { eof = 1; break; }
        }
    }

    return EXIT_SUCCESS;
}
