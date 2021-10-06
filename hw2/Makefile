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

hw2: hw2.c
	$(CC) -o word_guess.out hw2.c $(libunp) $(CFLAGS) -D $(MACRO)
