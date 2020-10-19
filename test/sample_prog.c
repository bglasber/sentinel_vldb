#include <stdlib.h>
#include <stdio.h>
#include "log.h"
#include "im_trace.h"
#include "impl.h"

void foo( int a ) {
    LOG( "In function call! %d\n", a );
}

int main( int argc, char **argv ) {
    init_im_tracing();

    LOG( "Starter log msg!\n", 0 );
    LOG( "Second msg: %d\n", 0 );

    foo( 5 );

    header_call();

    dump_im_tracing();
    return 0;
}
