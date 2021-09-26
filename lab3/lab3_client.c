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
#define	MAXLINE		    4096

// if client has less than 5 connections...
// use select() to connect to 127.0.0.1:port
// ignore input while connection in use
// print message when server disconnects
int main ()
{    
	int					i, maxi, maxfd, sockfd, port;
	int					nready, serv[MAX_CONNECTIONS];
	fd_set				rset, allset;
	char				buf[MAXLINE], new_port[10];
	struct sockaddr_in	servaddr;

    sockfd = Socket(AF_INET, SOCK_STREAM, 0);

    maxfd = sockfd;
	maxi = -1;					/* index into serv[] array */
	for (i = 0; i < MAX_CONNECTIONS; i++)
    {
		serv[i] = -1;			/* -1 indicates available entry */
    }

	FD_ZERO(&allset);
    FD_ZERO(&rset);

    // loop accepting port numbers via stdin 
	for ( ; ; ) 
    {   
        nready = Select(maxfd+1, &rset, NULL, NULL, NULL);

        // if total connections less than 6 connect to port
		if (FD_ISSET(sockfd, &rset) && maxi <= MAX_CONNECTIONS) 
        {   
            // stdin get port number
            if (FD_ISSET(fileno(stdin), &rset)) {  /* input is readable */
                if (Fgets(new_port, MAXLINE, stdin) == NULL)
                    continue;
                sscanf(new_port, "%d", &port);
            }

            sockfd = Socket(AF_INET, SOCK_STREAM, 0);

            bzero(&servaddr, sizeof(servaddr));
            servaddr.sin_family = AF_INET;
            servaddr.sin_port = htons(port);
            Inet_pton(AF_INET, "127.0.0.1", &servaddr.sin_addr);

            Connect(sockfd, (SA *) &servaddr, sizeof(servaddr));
			
            for (i = 0; i < FD_SETSIZE; i++)
				if (serv[i] < 0) {
					serv[i] = sockfd;	/* save descriptor */
					break;
				}
			if (i == FD_SETSIZE)
				continue;

			FD_SET(sockfd, &allset);	/* add new descriptor to set */
			if (sockfd > maxfd)
				maxfd = sockfd;			/* for select */
			if (i > maxi)
				maxi = i;				/* max index in serv[] array */

			if (--nready <= 0)
				continue;				/* no more readable descriptors */
		}

        // select setup
		FD_SET(fileno(stdin), &rset);
		FD_SET(sockfd, &rset);
		maxfd = max(fileno(stdin), sockfd) + 1;
		Select(maxfd, &rset, NULL, NULL, NULL);

        // message recieved from server, print to stdout
		if (FD_ISSET(sockfd, &rset)) {	/* socket is readable */
			if (Readline(sockfd, buf, MAXLINE) == 0)
				err_quit("str_cli: server terminated prematurely");
			Fputs(buf, stdout);
		}

    }

    return EXIT_SUCCESS;
}
