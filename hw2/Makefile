CC                    = clang
CFLAGS                = -Wall -pedantic
unpv13d_path_local_1  = ../unpv13e/libunp.a
unpv13d_path_local_2  = ../../unpv13e/libunp.a
unpv13d_path_submitty = libunp.a
HOST1                 = manjaro
HOST2                 = insert-hostmane

libunp = $(unpv13d_path_submitty)
MACROS  = -D SUBMITTY

ifeq ($(HOST1), $(shell hostname))
  libunp = $(unpv13d_path_local_1)
  MACROS  = -D DEV1 -D DEBUG
endif

ifeq ($(HOST2), $(shell hostname))
  libunp = $(unpv13d_path_local_2)
  MACROS  = -D DEV2 -D DEBUG
endif

hw2: hw2.c
	$(CC) -o word_guess.out hw2.c $(libunp) $(CFLAGS) $(MACROS)

clean:
	rm -f *.o *.out
