# This is what we use for Sentinel, in general.
#NEVENTS=1024

# This is what the unit tests use.
NEVENTS=64
all: libimtrace.a

libimtrace.a : im_trace.o
	ar rvs libimtrace.a im_trace.o

im_trace.o : im_trace.h im_trace.c
	#gcc -DNDEBUG -Wall -Werror -fPIC -O2 -c -g im_trace.c -DNEVENTS=$(NEVENTS)
	gcc -Wall -fPIC -c -g im_trace.c -DNEVENTS=$(NEVENTS)

clean:
	rm -rf *.o libimtrace.a

install :
	cp libimtrace.a /usr/local/lib
	mkdir -p /usr/local/include/imtrace
	cp im_trace.h /usr/local/include/imtrace

.PHONY:
	clean install
