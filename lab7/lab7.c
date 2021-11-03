//
//  lab7.c
//  NetProg lab7
//
//	Nate Bennett
// 	Anisha Halwai


#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/socket.h>
#include <netdb.h>
#include <errno.h>
#include <arpa/inet.h>
#include <limits.h>
#include <netinet/in.h>

#define BUF_SIZE 500
int main(int argc, const char * argv[]) {
	
	if(argc!=2) {
		fprintf(stderr,"Usage ./output.out hostname\n");
	}
	
    struct addrinfo hints, *result;
    struct addrinfo *res;
    int error;
    int sock;
    

    /* resolve the domain name into a list of addresses */
    memset(&hints,0,sizeof(hints));
    hints.ai_family = PF_UNSPEC;
    hints.ai_socktype = SOCK_DGRAM; //SOCK_STREAM?
    error = getaddrinfo(argv[1], NULL, &hints, &result);
    if (error != 0)
    {
        fprintf(stderr, "getaddrinfo failed, interpreting return status code: Name or service not known\n");
        perror("getaddrinfo failed, printing errno");
        exit(EXIT_FAILURE);
    }

    /* loop over all returned results and do inverse lookup */
    for (res = result; res != NULL; res = res->ai_next)
    {

        
		sock = socket(res->ai_family,res->ai_socktype,0);
		if(sock < 0){
			perror("ERROR: socket");
			exit(EXIT_FAILURE);
		}
		else{
			const char *ipverstr;
					
			switch (res->ai_family){
				case AF_INET:
					ipverstr = "IPv4";
					
					struct sockaddr_in *addr;
					addr = (struct sockaddr_in *)res->ai_addr;
					printf("%s\n",inet_ntoa((struct in_addr)addr->sin_addr));
					break;
				case AF_INET6:
					ipverstr = "IPv6";
					
					char buf[INET6_ADDRSTRLEN];
					struct sockaddr_in6 *in6 = (struct sockaddr_in6*)res->ai_addr;
					memcpy(buf, in6->sin6_addr.s6_addr, 16);
					
					if (inet_ntop(AF_INET6, &in6->sin6_addr.s6_addr, buf, sizeof(buf)) != NULL)
					   printf("%s\n", buf);
					else {
					   perror("inet_ntop");
					   exit(EXIT_FAILURE);
					}

					break;
				default:
					ipverstr = "unknown";
					break;
			}
		}
    }

    freeaddrinfo(result);
    return EXIT_SUCCESS;
}
