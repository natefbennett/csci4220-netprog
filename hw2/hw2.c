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

// adjust lib path if "DEV1" compiler macro used
// for nate
#ifdef DEV1
#include "../unpv13e/lib/unp.h"
#endif

// adjust lib path if "DEV2" compiler macro used
// for anisha
#ifdef DEV2
#include "../../unpv13e/lib/unp.h"
#endif

// adjust lib path if "SUBMITTY" compiler macro used
#ifdef SUBMITTY
#include "unp.h"
#endif

#define MAX_WORD_LENGTH 1024
#define MAX_MSG_LENGTH  2048
#define MAX_CONNECTIONS 5

int count_users = 0;
int count_clients = 0;

// structure for relating a name to clifd
typedef struct {
    int    clifd;  // client file descriptor
    char   name[MAX_WORD_LENGTH];
} user;

// structure for storing an array of all words
typedef struct {
    char ** words;
    int     size;
} dictionary;

// delete user from active users
// called once cli fd is closed
void DeleteUser( user * active, int clifd )
{
	for( int i = 0; i < MAX_CONNECTIONS; i++ )
	{
		if( active[i].clifd == clifd )
		{
			#ifdef DEBUG
			printf("DEBUG: deleting user -> active_users[%d]: \"%s\"\n", i, active[i].name);
			#endif
			
			memset(active[i].name, 0, MAX_WORD_LENGTH);
			active[i].clifd = -1;
			count_users--;

			break;
		}
	}
}

// adds a user to the user array supplied
void AddUser( user * active, int clifd, char * name )
{
	// find first empty slot to put user
	for( int i = 0; i < MAX_CONNECTIONS; i++ )
	{
		if( active[i].clifd == -1 )
		{
			strncpy(active[i].name, name, MAX_WORD_LENGTH);
			active[i].clifd = clifd;
			count_users++;

			#ifdef DEBUG
			printf("DEBUG: added new user -> active_users[%d]: \"%s\"\n", count_users-1, name);
			#endif 

			break;
		}
	}
}

bool ClientIsActiveUser( user * active, int clifd )
{
	for( int i = 0; i < MAX_CONNECTIONS; i++ ) {
		if( active[i].clifd == clifd ) {
			return true;
		}
	}
	return false;
}

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

int SetupServer( unsigned short port )
{
    struct sockaddr_in servaddr;
    int listenfd = Socket(AF_INET, SOCK_STREAM, 0);

	#ifdef DEBUG
	// solves error on binding, already in use
    int optval = 1;
    setsockopt(listenfd, SOL_SOCKET, SO_REUSEADDR, 
            	(const void *)&optval , sizeof(int));
	#endif

	bzero(&servaddr, sizeof(servaddr));
	servaddr.sin_family      = AF_INET;
	servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
	servaddr.sin_port        = htons(port);

	Bind(listenfd, (SA *) &servaddr, sizeof(servaddr));

	Listen(listenfd, LISTENQ);

    return listenfd;
}

// game method, find number of correct letters in guess
int GradeCorrect(char * word_guess, char * word)
{
	int letters_correct = 0;
	return letters_correct;
}

// game method, find number of correctly placed letters in guess
int GradePlacement(char * word_guess, char * word)
{
	int letters_placed = 0;
	return letters_placed;
}

int main ( int argc, char *argv[] )
{
	// NOTE: for Submitty (auto-grader) use only
    setvbuf( stdout, NULL, _IONBF, 0 );
    
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
	int					i, j, maxi, maxfd, connfd, sockfd, nready;
	int					client[FD_SETSIZE];
	ssize_t				n;					   // allset stores the original set since select is destructive
	fd_set				rset, allset;          // rset = ready sockets returned from select
	char				buf[MAX_WORD_LENGTH], msg[MAX_MSG_LENGTH];  
	struct sockaddr_in	cliaddr;
	socklen_t           clilen = sizeof(cliaddr);
    user                active_users[MAX_CONNECTIONS];

    // open supplied dictionary_file
    // read contents into array, preserving the order
    dictionary dict;
    dict.size = 0;
    dict.words = NULL;
    LoadWords( dictionary_file, &dict );
    unsigned int word_index = SelectWord( &dict, seed );

	// initialize active users
	for ( i = 0; i < MAX_CONNECTIONS; i++)
	{
		memset(active_users[i].name, 0, MAX_WORD_LENGTH);
		active_users[i].clifd = -1;
	}
	
    // bind to port and setup internet address for listening
    int listenfd = SetupServer( port );

	maxfd = listenfd;	 // initialize with current fd
	maxi = -1;	         // index into client[] array

	// setup client array for select
	// -1 indicates available entry
	for (i = 0; i < FD_SETSIZE; i++) {
		client[i] = -1;
	}
		
	FD_ZERO(&allset);
	FD_SET(listenfd, &allset);

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
    
	for ( ; ; ) 
	{
		/* 	when client joins: print welcome message
			ask for username
			store username
			if client 2 joins, ask for username, username should be unique
			once a client disconnects, delete their username from stored usernames
			
		*/
		rset = allset; // reset rset because is changed with every select() call
		nready = Select(maxfd+1, &rset, NULL, NULL, NULL);

		#ifdef DEBUG
		printf("DEBUG: new select() call -> nready: %d\n", nready);
		#endif
			
		// accept new client connection if max clients not reached
		if ( FD_ISSET(listenfd, &rset) && count_clients < MAX_CONNECTIONS ) 
		{
			connfd = Accept(listenfd, (SA *) &cliaddr, &clilen);

			#ifdef DEBUG
			printf("DEBUG: new connection recieved -> connfd: %d\n", connfd);
			#endif

			// find open slot to store new file descriptor
			for ( i = 0; i < FD_SETSIZE; i++ )
			{
				if ( client[i] < 0 ) {
					client[i] = connfd;
					break;
				}
			}
			count_clients++;
	
			if ( i == FD_SETSIZE ) {
				err_quit("FD_SETSIZE reached, too many clients");
			}

			#ifdef DEBUG
			printf("DEBUG: connection saved -> client[%d]: %d\n", i, connfd);
			#endif

			// send welcome message to new client
			strcpy(msg, "Welcome to Guess the Word, please enter your username.\n");
			Writen(connfd, msg, strlen(msg));

			FD_SET(connfd, &allset); // add new descriptor to allset

			// increase max file descriptor and max index if needed
			if ( connfd > maxfd ) {
				maxfd = connfd;
				#ifdef DEBUG
				printf("DEBUG: increased maxfd -> maxfd: %d\n", maxfd);
				#endif
			}
			if ( i > maxi ) {
				maxi = i; // max index in client[] array
				#ifdef DEBUG
				printf("DEBUG: increased maxi -> maxi: %d\n", maxi);
				#endif
			}

			// finished processing new file descriptor, decrement number of fd ready
			// call select again if no more descriptors are ready for reading
			if ( --nready <= 0 ) {
				#ifdef DEBUG
				printf("DEBUG: no more fd to read -> nready: %d\n\n", nready);
				#endif
				continue;
			}
		}

		// check all clients for data
		for (i = 0; i <= maxi; i++) 
		{
			// skip if no data
			if ( (sockfd = client[i]) < 0 ) {
				continue;
			}

			#ifdef DEBUG
			printf("DEBUG: data ready for reading -> client[%d]: %d\n", i, sockfd);
			#endif

			// process data from client
			if ( FD_ISSET(sockfd, &rset) )
			{
				// read from client and check for EOF
				if ( (n = Read(sockfd, buf, MAX_WORD_LENGTH)) == 0 )
				{
					#ifdef DEBUG
					printf("DEBUG: client disconnected -> client[%d]: %d\n", i, client[i]);
					#endif

					// deleting user from active_users and remove fd from allset
					DeleteUser(active_users, sockfd);
					Close(sockfd);
					FD_CLR(sockfd, &allset);
					client[i] = -1;
					count_clients--;

					#ifdef DEBUG
					printf("DEBUG: reset client slot -> client[%d]: %d\n", i, client[i]);
					#endif
				}
				else
				{
					buf[strcspn( buf, "\n" )] = 0; // strip newline

					#ifdef DEBUG
					printf("DEBUG: reading data from client -> client[%d]: %d\n", i, sockfd);
					#endif

					// check if client fd already exists in active users
					bool cli_exists = ClientIsActiveUser( active_users, sockfd );

					#ifdef DEBUG
					printf("DEBUG: client[%d]: %d in active users: %s\n", i, sockfd, cli_exists ? "TRUE" : "FALSE");
					#endif
					
					// user playing game
					if( cli_exists )
					{
						#ifdef DEBUG
						printf("DEBUG: user playing game -> active_users[%d]: %s\n", i, active_users[i].name );
						printf("       data received: \"%s\"\n", buf );
						printf("       target word:   \"%s\"\n", dict.words[word_index] );
						#endif

						// "Invalid guess length. The secret word is 5 letter(s)."
						if ( strlen(buf) != strlen(dict.words[word_index]) )
						{
							snprintf(msg, MAX_MSG_LENGTH, "Invalid guess length. The secret word is %lu letter(s).\n", strlen(dict.words[word_index]));
							Writen(sockfd, msg, strlen(msg));
						}

						int letters_correct = GradeCorrect(buf, dict.words[word_index]);
						int letters_placed = GradePlacement(buf, dict.words[word_index]);

						// send message to all user with info about guess
						for( j = 0; j < MAX_CONNECTIONS; j++ )
						{
							if( active_users[j].clifd != -1 )
							{
								// check if word guess was correct
								if ( letters_correct == strlen(dict.words[word_index]) )
								{
									// print out Z has correctly guessed the word S
									// delete user and disconnect client
									// restart game with new word
								}
								
								// word guess was incorrect
								snprintf(msg, MAX_MSG_LENGTH, "%s guessed %s: %d letter(s) were correct and %d letter(s) were correctly placed.\n", active_users[i].name, buf, letters_correct, letters_placed);
								Writen(active_users[j].clifd, msg, strlen(msg));
							}
						}
						continue;
					}
					
					bool username_exist = false;

					// client not yet added to active_users
					if( !cli_exists ) 
					{
						// new client, check if requested username taken 
						for( j = 0; j < MAX_CONNECTIONS; j++ ) {
							
							// buf holds requested username
							if( strcmp( active_users[j].name, buf ) == 0 )
							{
								#ifdef DEBUG
								printf("DEBUG: username \"%s\" already taken by active_user[%d]\n", buf, j);
								#endif

								// send message to client, ask for different username
								snprintf(msg, MAX_MSG_LENGTH, "Username %s is already taken, please enter a different username\n", buf);
								Writen(sockfd, msg, strlen(msg));

								username_exist = true;
								break;
							}
						}
					}
					
					// username not taken, store username and client fd in active_users
					if( !username_exist )
					{
						#ifdef DEBUG
						printf("DEBUG: valid user name -> adding \"%s\" to active_users[%d]\n", buf, count_users);
						#endif 

						// send message to client, username accepted
						memset(msg, 0, MAX_MSG_LENGTH);
						snprintf(msg, MAX_MSG_LENGTH,"Let's start playing, %s\n", buf);
						Writen(sockfd, msg, strlen(msg));

						AddUser(active_users, sockfd, buf);

						// send game stats to new user
						memset(msg, 0, MAX_MSG_LENGTH);
						snprintf(msg, MAX_MSG_LENGTH,"There are %d player(s) playing. The secret word is %lu letter(s).\n", count_users, strlen(dict.words[word_index]));
						Writen(sockfd, msg, strlen(msg));
					}
				}
				
				// no more readable file descriptors
				if ( --nready <= 0 ) {
					#ifdef DEBUG
					printf("DEBUG: no more fd to read -> nready: %d\n\n", nready);
					#endif
					break;
				}	
			}
		}
	}

    RemoveWords( &dict );
    return EXIT_SUCCESS;
}
