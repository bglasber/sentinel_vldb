#ifndef __LOG_H__
#define __LOG_H__
#define LOG( msg, ... ) \
    log_message( __FILE__, __LINE__, msg, __VA_ARGS__ )

// Format message and dump to stdout
//
void log_message( const char *fname, int line_number, const char *fmt_msg, ... );
#endif
