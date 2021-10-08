// Author(s): Nate Bennett, Anisha Halwai
// Date:      10/18/21
// File:      hw2.c
//
// Assignment 2
// CSCI 4220: Network Programming
// Professor Jasmine Plum

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include "../../unpv13e/lib/unp.h"

// adjust lib path if "DEV" compiler macro used
#ifdef DEV
#include "../unpv13e/lib/unp.h"
#endif

// adjust lib path if "SUBMITTY" compiler macro used
#ifdef SUBMITTY
#include "unp.h"
#endif

#define MAX_WORD_LENGTH 1024
#define MAX_CONNECTIONS 5

// structure for relating a name to clifd
typedef struct {
    int    clifd;  // client file descriptor
    char * name;
} user;

// structure for storing an array of all words
typedef struct {
    char ** words;
    int     size;
} dictionary;

// garbage collection for dictionary
void RemoveWords( dictionary * dict )
{
    for(int i = 0; i < dict->size; i++) {
        free(dict->words[i]);
    }
    free(dict->words);
    dict->words = NULL;
    dict->size = 0;
}

unsigned int SelectWord( dictionary * dict, unsigned int seed )
{
    srand(seed);
    return rand() % dict->size;
}

void LoadWords( char * filename, dictionary * dict )
{
    FILE *  fp;
    char *  line = NULL;
    size_t  len  = 0;
    ssize_t read;

    fp = fopen(filename, "r");
    if ( fp == NULL ) {
        perror("Error opening file: ");
        exit(EXIT_FAILURE);
    }
    
    // go through file line by line,
    // reallocating words array for each word added
    while ( (read = getline(&line, &len, fp)) != -1 ) {

        // allocations for pointer to word array
        if ( dict->size == 0 ) {
            dict->words = calloc( 1, sizeof(char *) );
        }
        else {
            dict->words = realloc( (void *)dict->words, (dict->size+1)*sizeof(char *) );
        }
        
        // allocate for new word of size read
        dict->words[dict->size] = calloc( read, sizeof(char) );
        line[strcspn( line, "\n" )] = 0; // strip newline

        // copy string into allocated memory
        strncpy( dict->words[dict->size], line, read );
        dict->size++; // we have added a word
    }

    fclose(fp);
    if (line) { free(line); } // better safe then sorry according to getline man page
}

int main ( int argc, char *argv[] )
{
    
    if ( argc != 5 ) {
        fprintf( stderr, "Usage: %s [seed] [port] [dictionary_file] [longest_word_length]\n", argv[0] );
        return EXIT_FAILURE;
    }
    
    // assign command line args without error checking integer overflow
    unsigned int                  seed = atoi(argv[1]);
    unsigned short                port = atoi(argv[2]);
    unsigned short longest_word_length = atoi(argv[4]);
    char *             dictionary_file =      argv[3];
    

    // networking variables
	int					i, maxi, maxfd, listenfd, connfd, sockfd, nready;
	int					client[FD_SETSIZE];
	ssize_t				n;
	fd_set				rset, allset;          // rset = ready sockets returned from select
	char				buf[MAX_WORD_LENGTH];  // allset stores the original set since select is destructive
	socklen_t			clilen;
	struct sockaddr_in	cliaddr, servaddr;
    user                active_users[MAX_CONNECTIONS];

    // open supplied dictionary_file
    // read contents into array, preserving the order
    dictionary dict;
    dict.size = 0;
    dict.words = NULL;
    LoadWords( dictionary_file, &dict );
    unsigned int word_index = SelectWord( &dict, seed );

    // bind to port and setup internet address for listening
    listenfd = Socket(AF_INET, SOCK_STREAM, 0);

	bzero(&servaddr, sizeof(servaddr));
	servaddr.sin_family      = AF_INET;
	servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
	servaddr.sin_port        = htons(SERV_PORT);

	Bind(listenfd, (SA *) &servaddr, sizeof(servaddr));

	maxfd = listenfd;			/* initialize */
	maxi = -1;					/* index into client[] array */
	for (i = 0; i < FD_SETSIZE; i++)
		client[i] = -1;			/* -1 indicates available entry */
	FD_ZERO(&allset);
	FD_SET(listenfd, &allset);
    // setup client array for select

    // server loop
	/*
    for ( ; ; )
    {

        bool game_won = false;

        // game loop
        while ( !game_won )
        {
            // welcome new client connection
            // username case insensitive
            printf("Welcome to Guess the Word, please enter your username.\n");
        }

    }
    */
    
	for ( ; ; ) {
			/* 	when client joins: print welcome message
				ask for username
				store username
				if client 2 joins, ask for username, username should be unique
				once a client disconnects, delete their username from stored usernames
				
			*/
			rset = allset;		/* structure assignment */
			nready = Select(maxfd+1, &rset, NULL, NULL, NULL);
			if (FD_ISSET(listenfd, &rset) && maxi <= MAX_CONNECTIONS){
				
				if (FD_ISSET(listenfd, &rset)) {	/* new client connection */
					
					//welcome message
					printf("Welcome to Guess the Word, please enter your username.\n");
					
					clilen = sizeof(cliaddr);
					connfd = Accept(listenfd, (SA *) &cliaddr, &clilen);


					for (i = 0; i < FD_SETSIZE; i++)
						if (client[i] < 0) {
							client[i] = connfd;	/* save descriptor */
							break;
						}
					if (i == FD_SETSIZE)
						err_quit("too many clients");

					FD_SET(connfd, &allset);	/* add new descriptor to set */
					if (connfd > maxfd)
						maxfd = connfd;			/* for select */
					if (i > maxi)
						maxi = i;				/* max index in client[] array */

					if (--nready <= 0)
						continue;				/* no more readable descriptors */
				}

				for (i = 0; i <= maxi; i++) {	/* check all clients for data */
					if ( (sockfd = client[i]) < 0){
						continue;
					}
					if (FD_ISSET(sockfd, &rset)) {
						//read from client
						if ( (n = Read(sockfd, buf, MAXLINE)) == 0) {
								/*4connection closed by client */
							Close(sockfd);
							FD_CLR(sockfd, &allset);
							client[i] = -1;
						} else
							/*check if username already exists
							  loop to check if client file descriptor already exists in active users
							  if yes: data is part of game
							  if no: data is username, store file descriptor
							*/
							for(int i=0; i<MAX_CONNECTIONS; i++){
								
							}
							Writen(sockfd, buf, n);

						if (--nready <= 0)
							break;				/* no more readable descriptors */
					}
				}
			}
		}
    RemoveWords( &dict );
    return EXIT_SUCCESS;
}
