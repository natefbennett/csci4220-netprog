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

int main ()
{
    int num_connections = 0;
    // read in port from stdin
    // if client has less than 5 connections...
    // use select() to connect to 127.0.0.1:port
    // ignore input while connection in use
    // print message when server disconnects
    return EXIT_SUCCESS;
}