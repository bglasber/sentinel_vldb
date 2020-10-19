CC=gcc
CFLAGS=-DACEUNIT_SUITES -I/usr/local/include/imtrace/ -I/usr/local/include/aceunit/
LDFLAGS=-L/usr/local/lib -limtrace -laceunit -lpthread -lm

all : sample_prog test_same_file_log

test_same_file_log : test_same_file_log.o log.o module.o Suite1.o
	$(CC) $(CFLAGS) test_same_file_log.o log.o module.o Suite1.o -o test_same_file_log  $(LDFLAGS)

module.o : module.c module.h
	$(CC) $(CFLAGS) -c module.c $(LDFLAGS)

Suite1.o : Suite1.c
	$(CC) $(CFLAGS) -c Suite1.c $(LDFLAGS)

test_same_file_log.o : test_same_file_log.c
	java -jar AceUnit.jar test_same_file_log >test_same_file_log.h
	$(CC) $(CFLAGS) -c test_same_file_log.c  $(LDFLAGS)

sample_prog : sample_prog.o log.o
	$(CC) $(CFLAGS) sample_prog.o log.o -o sample_prog $(LDFLAGS)

sample_prog.o : sample_prog.c
	$(CC) $(CFLAGS) -c sample_prog.c $(LDFLAGS)

log.o : log.c log.h
	$(CC) $(CFLAGS) -c log.c $(LDFLAGS)

clean :
	rm -rf sample_prog test_same_file_log *.o

.PHONY:
	sample_prog clean
