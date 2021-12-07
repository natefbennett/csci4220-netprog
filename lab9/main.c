//
//  main.c
//  lab9
//
//  Created by Anisha Halwai on 06/12/21.
//  Copyright © 2021 Anisha Halwai. All rights reserved.
//

#include <netinet/tcp.h>
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

int main(int argc, const char * argv[]) {
	if(argc!=2) {
		fprintf(stderr,"Usage ./output.out hostname\n");
	}
	
	//print mms and recieve buffer size
	int sockfd, mss;

    if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        perror("sockfd");
        return 1;
    }

    socklen_t len = sizeof(mss);
    if (getsockopt(sockfd, IPPROTO_TCP, TCP_MAXSEG, &mss, &len) < 0)
    {
        perror("getsockopt");
        return 1;
    }
//    char buff[256] = {0};
//	size_t l = 0;
//	ssize_t n = recv(sockfd, buff,l, 0);
    printf("maximum segment size: %d\n", mss);
	printf("recieve buffer size: %u\n", len);
    
    struct sockaddr_in servaddr;
	memset(&servaddr, 0, sizeof(servaddr));
	servaddr.sin_family = AF_INET;
	servaddr.sin_port = htons(80);
	servaddr.sin_addr.s_addr = inet_addr(argv[1]);
	
    if(connect(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr)) <0){
		perror("connect");
	}
//	n = recv(sockfd, buff,l,10);
	
	len = sizeof(mss);
    if (getsockopt(sockfd, IPPROTO_TCP, TCP_MAXSEG, &mss, &len) < 0)
    {
        perror("getsockopt");
        return 1;
    }
//    l=0;
	
    printf("maximum segment size: %d\n", mss);
	printf("recieve buffer size: %u\n", len);
    close(sockfd);
	return 0;
}
