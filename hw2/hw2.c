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

void LoadWords( char * filename, dictionary * dict )
{
    FILE *  fp;
    char *  line = NULL;
    size_t  len  = 0;
    ssize_t read;

    fp = fopen(filename, "r");
    if ( fp == NULL ) {
        perror("Error opening file %s: ", filename);
        exit(EXIT_FAILURE);
    }
    
    // allocate memory for words array

    // go through file line by line,
    // reallocating words array for each word added
    while ( (read = getline(&line, &len, fp)) != -1 ) {
        // realloc word array
        // allocate for new word of size read
        printf("Retrieved line of length %zu:\n", read);
        printf("%s", line);
    }

    fclose(fp);
    if (line) { free(line); }
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
	ssize_t				n;
	fd_set				rset, allset;
	char				buf[MAX_WORD_LENGTH];
	socklen_t			clilen;
	struct sockaddr_in	cliaddr, servaddr;    
    user                active_users[MAX_CONNECTIONS];

    // open supplied dictionary_file
    // read contents into array, preserving the order
    dictionary dict;
    LoadWords( dictionary_file, &dict );

    // bind to port and setup internet address for listening
    listenfd = Socket(AF_INET, SOCK_STREAM, 0);

	bzero(&servaddr, sizeof(servaddr));
	servaddr.sin_family      = AF_INET;
	servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
	servaddr.sin_port        = htons(SERV_PORT);

	Bind(listenfd, (SA *) &servaddr, sizeof(servaddr));

	Listen(listenfd, LISTENQ);

    // setup client array for select

    // server loop
    for ( ; ; )
    {

        // srand(seed) then rand() % dictionary_size

        bool game_won = false;

        // game loop 
        while ( !game_won )
        {
            // welcome new client connection
            // username case insensitive
            printf("Welcome to Guess the Word, please enter your username.\n");
        }

    }


    return EXIT_SUCCESS;
}