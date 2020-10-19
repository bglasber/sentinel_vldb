#include "log.h"

int header_line = 0;
char *header_file;

void header_log( void ) {
    LOG( "Test Log message!\n", 0 ); header_line = __LINE__;
    header_file = __FILE__;
}

int get_header_log_line() {
    return header_line;
}

char *get_header_file() {
    return header_file;
}
