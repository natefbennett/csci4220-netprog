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
#define TIMEOUT     10

// read in line of input and send to client
void SendLine(FILE *fp, int sockfd)
{
	int			maxfdp1;
	fd_set		rset;
	char		sendline[MAXLINE], recvline[MAXLINE];

	FD_ZERO(&rset);
	for ( ; ; ) {
		FD_SET(fileno(fp), &rset);
		FD_SET(sockfd, &rset);
		maxfdp1 = max(fileno(fp), sockfd) + 1;
		Select(maxfdp1, &rset, NULL, NULL, NULL);

		if (FD_ISSET(sockfd, &rset)) {	/* socket is readable */
			if (Readline(sockfd, recvline, MAXLINE) == 0)
				err_quit("str_cli: server terminated prematurely");
			Fputs(recvline, stdout);
		}

		if (FD_ISSET(fileno(fp), &rset)) {  /* input is readable */
			if (Fgets(sendline, MAXLINE, fp) == NULL)
				return;		/* all done */
			Writen(sockfd, sendline, strlen(sendline));
		}
	}
}

int main ( int argc, char *argv[] )
{
    int port = atoi(argv[1]) + START_PORT;

    int					sockfd;
	struct sockaddr_in	servaddr;

	if (argc != 2)
		err_quit("usage: %s <port>", argv[0]);

	sockfd = Socket(AF_INET, SOCK_STREAM, 0);

	bzero(&servaddr, sizeof(servaddr));
	servaddr.sin_family = AF_INET;
	servaddr.sin_port = htons(port);
	Inet_pton(AF_INET, "127.0.0.1", &servaddr.sin_addr);

	Connect_timeo(sockfd, (SA *) &servaddr, sizeof(servaddr), TIMEOUT);

    // read in stdin
    // if EOF close connection
	SendLine(stdin, sockfd);	

    return EXIT_SUCCESS;
}