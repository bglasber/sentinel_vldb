#include "log.h"
#include "module.h"

static int log_line1;
static int log_line2;
static const char* fname = __FILE__;

void ofile_func_call1( int a, int b ) {
    LOG( "Made a call in another file: %d, %d\n", a, b ); log_line1 = __LINE__;
}

void ofile_func_call2( double d ) {
    LOG( "Func call2 in another file: %f\n", d ); log_line2 = __LINE__;
}

int get_ofile_log_line1() {
    return log_line1;
}

int get_ofile_log_line2() {
    return log_line2;
}

const char* get_ofile_fname() {
    return fname;
}
