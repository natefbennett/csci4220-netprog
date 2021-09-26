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

#define MAX_CONNECTIONS 5

int main ()
{

    // read in port from stdin
    char buffer[5]; // max port 5 digits: 65535
    int port;

    while(fgets(buffer, sizeof buffer, stdin) != NULL) {
        if(sscanf(buffer, "%d", &port) == 1) {
            break;
        }
    }

    // if client has less than 5 connections...
    // use select() to connect to 127.0.0.1:port
    // ignore input while connection in use
    // print message when server disconnects


	int					i, maxi, maxfd, listenfd, connfd, sockfd;
	int					nready, serv[MAX_CONNECTIONS];
	ssize_t				n;
	fd_set				rset, allset;
	char				buf[MAXLINE];
	socklen_t			clilen;
	struct sockaddr_in	cliaddr, servaddr;

	listenfd = Socket(AF_INET, SOCK_STREAM, 0);

	bzero(&servaddr, sizeof(servaddr));
	servaddr.sin_family      = AF_INET;
	servaddr.sin_addr.s_addr = inet_addr("127.0.0.1");
	servaddr.sin_port        = htons(port);

	Bind(listenfd, (SA *) &servaddr, sizeof(servaddr));

	Listen(listenfd, LISTENQ);

	maxfd = listenfd;			/* initialize */
	maxi = -1;					/* index into client[] array */
	for (i = 0; i < 5; i++)
		serv[i] = -1;			/* -1 indicates available entry */
	FD_ZERO(&allset);
	FD_SET(listenfd, &allset);
/* end fig01 */

/* include fig02 */
	for ( ; ; ) {
		rset = allset;		/* structure assignment */
		nready = Select(maxfd+1, &rset, NULL, NULL, NULL);

		if (FD_ISSET(listenfd, &rset)) {	/* new server connection */
			clilen = sizeof(cliaddr);
			connfd = Accept(listenfd, (SA *) &cliaddr, &clilen);

			printf("new server: %s, port %d\n",
					Inet_ntop(AF_INET, &cliaddr.sin_addr, 4, NULL),
					ntohs(cliaddr.sin_port));

			for (i = 0; i < MAX_CONNECTIONS; i++)
				if (serv[i] < 0) {
					serv[i] = connfd;	/* save descriptor */
					break;
				}
			if (i == MAX_CONNECTIONS)
				err_quit("too many servers");

			FD_SET(connfd, &allset);	/* add new descriptor to set */
			if (connfd > maxfd)
				maxfd = connfd;			/* for select */
			if (i > maxi)
				maxi = i;				/* max index in serv[] array */

			if (--nready <= 0)
				continue;				/* no more readable descriptors */
		}
	
		// if(maxi<MAX_CONNECTIONS){
		// 	//connect to port from stdin

		// }
		for (i = 0; i <= maxi; i++) {	/* check all servers for data */
			if ( (sockfd = serv[i]) < 0)
				continue;
			if (FD_ISSET(sockfd, &rset)) {
				if ( (n = Read(sockfd, buf, MAXLINE)) == 0) {
						/*4connection closed by client */
					Close(sockfd);
					FD_CLR(sockfd, &allset);
					serv[i] = -1;
					printf("Connection closed port %d\n", port);
				} else
					Writen(sockfd, buf, n); /* Write "n" bytes to a descriptor. */
					//write to stdout if Writen isnt already
				if (--nready <= 0)
					break;				/* no more readable descriptors */
			}
		}
	}


    return EXIT_SUCCESS;
}
