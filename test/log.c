#include "log.h"
#include "im_trace.h"
#include <stdio.h>
#include <stdarg.h>

void log_message( const char *fname, int line_number, const char *fmt_msg, ... ){
    record_event( fname, line_number );
    va_list ap;
    char newfmt[1024] = { 0 };
    va_start( ap, fmt_msg );
    sprintf( newfmt, "[INFO] (%s:%d): %s", fname, line_number, fmt_msg );
    //vfprintf( stderr, newfmt, ap );
    va_end( ap );
}
