CC                    = clang
CFLAGS                = -Wall -pedantic
unpv13d_path_local    = ../unpv13e/libunp.a
unpv13d_path_submitty = libunp.a
HOST1                 = manjaro
HOST2                 = insert-hostmane

libunp = $(unpv13d_path_submitty)
MACRO  = SUBMITTY

ifeq ($(HOST1), $(shell hostname))
  libunp = $(unpv13d_path_local)
  MACRO  = DEV
endif

ifeq ($(HOST2), $(shell hostname))
  libunp = $(unpv13d_path_local)
  MACRO  = DEV
endif

default: client server

client: lab3_client.c
	$(CC) lab3_client.c $(libunp) -o lab3_client.out $(CFLAGS) -D $(MACRO)

server: lab3_server.c
	$(CC) lab3_server.c $(libunp) -o lab3_server.out $(CFLAGS) -D $(MACRO)

clean:
	rm -f *.o *.out
