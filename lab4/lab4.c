// Author(s): Nate Bennett, Anisha Halwai 
// Date:      10/05/21
// File:      lab4.c
//
// Lab 4
// CSCI 4220: Network Programming
// Professor Jasmine Plum

// Notes:
// -- recusive add function no pthread
// int add(int a, int b) { 
//     if ( b ) {
//         return 1 + add( a, b-1 );
//     } else {
//         return a;
//     }
// } 

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

typedef struct {
    int a, b, sum;
} pair;

// pass in pointer pair struct as void pointer
void * add( void * v )
{
    pair *p = (pair*)v; 
    
    if ( p->b ) {
        p->sum += 1;
        p->b   -= 1;
        return add( (void*)p );
    } else {
        return p;
    }     
}

int main ( int argc, char *argv[] )
{
    if ( argc != 2 ) {
        fprintf( stderr, "Error: Incorrect usage: %s <MAX_ADDAND>\n", argv[0] );
        return EXIT_FAILURE;
    }

    const unsigned int MAX_ADDAND = atoi(argv[1]);
    const unsigned int TOTAL_CHILDREN = ((MAX_ADDAND-1) * MAX_ADDAND );

    // multi-threaded solution to...
    // add every combination of numbers [1…(MAX_ADDAND-1)] 
    //  to every combination of numbers [1 … MAX_ADDAND]

    pthread_t children[TOTAL_CHILDREN];
    pair *pair_ptrs[TOTAL_CHILDREN];

    // loop through [1…(MAX_ADDAND-1)]
    unsigned int index = 0; // store child pthread_t array and pair_ptrs
    unsigned int i, j;
    for ( i = 1; i < MAX_ADDAND; i++ )
    {
        // loop through [1…(MAX_ADDAND)]
        for ( j = 1; j < MAX_ADDAND+1; j++, index++ )
        {
            printf( "Main starting thread add() for [%d + %d]\n", i, j );

            // allocate pair struct instance and save pointer for free()
            pair *pair_ptr = calloc( 1, sizeof(pair) );
            pair_ptrs[index] = pair_ptr;
            
            // store i and j as pair { a, b } 
            // sum in initialized to the same value as a
            pair_ptr->a   = i;
            pair_ptr->b   = j;
            pair_ptr->sum = i;

            // create thread to handle adding a and b
            pthread_t tid;
            int val = pthread_create(&tid, NULL, add, (void*)pair_ptr);
            
            if (val < 0) {
                fprintf( stderr, "Error %d: could not create thread\n", val );
                return EXIT_FAILURE;
            } 
            else {
                printf("Thread %lu running add() with [%d + %d]\n", tid, i, j);
                children[index] = tid;
            }

        }
    }

    // print addition results from threads
    for ( i = 0; i < TOTAL_CHILDREN; i++ )
    {
        pair *ret_val;
        pthread_join( children[i], (void**)&ret_val );

        int b = ret_val->sum - ret_val->a;
        printf( "In main, collecting thread %lu computed [%d + %d] = %d\n", 
                                    children[i],  ret_val->a,  b,   ret_val->sum );
    }

    // clean up allocated heap memory
    for ( i = 0; i < TOTAL_CHILDREN; i++ ) {
        free( pair_ptrs[i] );
    }

    return EXIT_SUCCESS;
}
