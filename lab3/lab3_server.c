#include <stdio.h>
#include <stdlib.h>
#include "../unpv13e/lib/unp.h"

#define START_PORT 9877

int main ( int argc, char *argv[] )
{
    int port = atoi(argv[1]) + START_PORT;

    // read in stdin
    // if EOF close connection

    return EXIT_SUCCESS;
}