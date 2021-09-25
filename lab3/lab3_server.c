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

#define START_PORT 9877

int main ( int argc, char *argv[] )
{
    int port = atoi(argv[1]) + START_PORT;

    // read in stdin
    // if EOF close connection

    return EXIT_SUCCESS;
}