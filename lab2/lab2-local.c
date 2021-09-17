#include <stdio.h>
#include <stdlib.h>
#include "../unpv13e/lib/unp.h"

int Child()
{
    pid_t pid = getpid();

    // srand( time(NULL) * pid ); // seed random num generator
    srand( pid );
    int t = 1 + ( rand() % 5 );
    
    printf("Child PID %d dying in %d seconds.\n", pid, t);
    sleep( t );
    printf("Child PID %d terminating.\n", pid);

    return t;
}

void SigHandler()
{
    int stat;
    pid_t pid;
    while ((pid = waitpid(-1, &stat, WNOHANG)) > 0)
    {
        printf("Parent sees child PID %d has terminated.\n", pid);
    }
}

int main ()
{
    // NOTE: for Submitty (auto-grader) use only
    setvbuf( stdout, NULL, _IONBF, 0 ); 
      
    int num_children = 0;

    printf( "Number of children to spawn: " );
    scanf("%d", &num_children);
    printf("Told to spawn %d children\n", num_children);

    Signal(SIGCHLD, SigHandler);

    for (int i = 0; i < num_children; i++)
    {
        pid_t pid = fork();

        if ( pid == -1 )
        {
            perror( "fork() failed" );
            return EXIT_FAILURE;
        }
        else if ( pid == 0 ) // child
        {
            // free( pids );
            int rc = Child( );
            exit( rc );
        }
        else if ( pid > 0 ) // parent
        {
            printf("Parent spawned child PID %d\n", pid);
        }

    }
    for (int i = 0; i < num_children; i++)
    {
        sleep(6);
    }
    
    return EXIT_SUCCESS;
}