#include "im_trace.h"
#include <stdint.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <pthread.h>
#include <math.h>

#define RAND_RANGE 32767

// The fastrand functions have a range of 0-32767. If reservoir size is larger, then
// samples are no longer uniformly random.
static_assert( RESERVOIR_SIZE < RAND_RANGE, "Reservoir size must be less than PRNG range" );

/* 
 * Per-thread content: PostgreSQL uses C89 so we rely on GCC __thread rather than more recent thread_local_storage
 * Contains event counts, transition counts, records that describe events, and some flag variables to indicate state.
 * Fixed number of events defined by NEVENTS to avoid an extra pointer indirection.
 * These matrices are quite sparse. If space is a concern, then we can revisit with sparse matrix libraries to reduce overhead
 */
const uint64_t NANO = 1000 * 1000 * 1000;

static __thread uint64_t last_recorded_time = 0;
static __thread uint64_t g_seed;
static __thread int      should_record_transition_time = 0;

// The last event we recorded, for transition purposes
static __thread int last_event_ind = -1;

static __thread EventRegInfo event_info[NEVENTS];

// If we ran out of event slots, set this to indicate a problem
static __thread int overflow = 0;

// The file descriptor that we should dump the trace to at the end
static __thread int out_fd = -1;

//static __thread int special_fd = -1;

// The name of the file that we should dump the trace to at the end
static __thread char out_file_name[64];

// Indicates if we re in the fork handler.
static __thread int in_fork_handler = 0;

/*
 * rotate_left
 * rotating left shift
 */
static inline uint64_t rotate_left( uint64_t val, int shift ) {
    return (val << shift ) | ( val >> (64-shift) );
}


// Technically, this is ordered. We can short circuit.
#define find_relevant_list_entry( base_ptr, event_id ) \
    while( base_ptr != NULL ) { \
        if( base_ptr->event_id == event_id ) { \
            break; \
        } \
        base_ptr = base_ptr->next; \
    } \
    (void) base_ptr

/*
 * get_relevant_reservoir
 * Given a linked list of reservoirs, walk through them until we find the reservoir corresponding
 * to the given event ID.
 */
static Reservoir *get_relevant_reservoir( Reservoir *reservoir, int event_id ) {
    find_relevant_list_entry( reservoir, event_id );
    return reservoir;
}

/*
 * get_relevant_transition
 * Given a linked list of transitions, walk through them until we find the transition corresponding
 * to the given event ID.
 */
static TransitionCount *get_relevant_transition( TransitionCount *transition, int event_id ) {
    find_relevant_list_entry( transition, event_id );
    return transition;
}

EventRegInfo *get_event_reg_infos() {
    return event_info;
}

/*
 * alloc_new_reservoir_internal()
 * malloc the Reservoir struct and set up the fields
 */
static Reservoir *alloc_new_reservoir_internal( int event_id ) {
    Reservoir *ptr = (Reservoir *) malloc( sizeof( Reservoir ) );
    ptr->event_id = event_id;
    ptr->next_slot = 0;
    for( int i = 0; i < RESERVOIR_SIZE; i++ ) {
        ptr->value_pool[i] = 0.0;
    }
    return ptr;
}

// Macro to insert an allocated element for event_id into a ptr_type list at event_info->ptr_name using
// alloc_func. Enforces ascending order of event_ids.
#define alloc_new_list_entry( event_info, ptr_type, ptr_name, event_id, alloc_func ) \
    if( event_info->ptr_name == NULL ) { \
        event_info->ptr_name = alloc_func( event_id ); \
        event_info->ptr_name->next = NULL; \
        return event_info->ptr_name; \
    } \
    ptr_type *prev = NULL; \
    ptr_type *cur = event_info->ptr_name; \
    while( cur != NULL ) { \
        if( cur->event_id >= event_id ) { \
            ptr_type *ptr = alloc_func( event_id ); \
            ptr->next = cur; \
            if( prev == NULL ) { \
                event_info->ptr_name = ptr; \
            } else { \
                prev->next = ptr; \
            } \
            return ptr; \
        } \
        prev = cur; \
        cur = cur->next; \
    } \
    ptr_type *ptr = alloc_func( event_id ); \
    ptr->next = NULL; \
    prev->next = ptr; \
    return ptr 

/*
 * alloc_new_reservoir
 * allocate a new reservoir and link it into the linked list of reservoirs
 */
static Reservoir *alloc_new_reservoir( EventRegInfo *event_info, int event_id ) {
    alloc_new_list_entry( event_info, Reservoir, reservoir_ptr, event_id, alloc_new_reservoir_internal );
}

/*
 * alloc_new_transition_internal()
 * alloc function for a transition.
 */
static TransitionCount *alloc_new_transition_internal( int event_id ) {
    TransitionCount *ptr = (TransitionCount *) malloc( sizeof( TransitionCount ) );
    ptr->event_id = event_id;
    ptr->count = 0;
    return ptr;
}


/*
 * alloc_new_transition
 * allocate a new transition and link it into the linked list of transitions 
 */
static TransitionCount *alloc_new_transition( EventRegInfo *event_info, int event_id ) {
    alloc_new_list_entry( event_info, TransitionCount, transition_ptr, event_id, alloc_new_transition_internal );
}

/*
 * fast_srand
 * Seed the fast random number generator with the given seed
 */
static inline void fast_srand( int seed ) {
    g_seed = seed;
}

/*
 * fastrand
 * Returns one pseudo-random integer, output range [0-32767]
 */
static inline int fastrand() {
    g_seed = (214013*g_seed+2531011);
    return (g_seed>>16)&0x7FFF;
}

/*
 * add_norm_ticks_to_reservoir
 * Given a reservoir ptr and a normalized tick count, add the ticks to the reservoir.
 * Replaces an entry at random if full
 */
static void add_norm_ticks_to_reservoir( Reservoir *reservoir, double norm_ticks ) {

    // If we don't need to replace values yet, don't!
    if( reservoir->next_slot < RESERVOIR_SIZE ) {
        reservoir->value_pool[reservoir->next_slot] = norm_ticks;
        reservoir->next_slot++;
        return;
    }

    // Randomly replace one of the values
    int ind = fastrand() % RESERVOIR_SIZE;
    reservoir->value_pool[ind] = norm_ticks;
}

/*
 * record_elapsed_ticks
 * Find the reservoir corresponding to the transition time between last_event_ind and
 * cur_event_id, add norm_ticks to it.
 */
static void record_elapsed_ticks( int last_event_id, int cur_event_id, double norm_ticks ) {

    Reservoir *reservoir = event_info[last_event_id].reservoir_ptr;
    reservoir = get_relevant_reservoir( reservoir, cur_event_id );

    if( reservoir == NULL ) {
        reservoir = alloc_new_reservoir( &(event_info[last_event_id]), cur_event_id );
    }

    assert( reservoir != NULL );
    add_norm_ticks_to_reservoir( reservoir, norm_ticks );
}

/*
 * write_to_file
 * Given a file descriptor and a buffer, write wrlen bytes from the buffer
 * to the fd, looping as necessary until it is done.
 */
static void write_to_file( int fd, char *buff, int wrlen ) {
    int wr_thus_far = 0;
    if( wrlen > 0 ) { 
        int write_ret = 0; 
        while( wr_thus_far < wrlen ) {
            write_ret = write( fd, buff+wr_thus_far, wrlen-wr_thus_far );
            if( write_ret == -1 ) {
                printf( "Could not write to file. Got error code: %d\n", errno );
                return;
            }
            wr_thus_far += write_ret;
        }
    }
}

/* normalize()
 * Take the ticks value and normalize by 10^4
 */
static inline double normalize( uint64_t ticks ) {
    return ((double)ticks) / (double) 10000.0;
}


void im_fork();

/* get_overflow()
 * Determine if we are out of event slots.
 */
int get_overflow() {
    return overflow;
}

/*
 * get_nevents()
 * Return the number of events we can track, used as bounds on the tracking arrays 
 */
int get_nevents() {
    return NEVENTS;
}


/*
 * init_im_tracing()
 * Initialize in memory tracing. When called, initializes all of the memory allocated for 
 * this thread's in memory tracing components.
 */
void init_im_tracing() {

    int i;
    pid_t my_pid;
    pid_t my_tid;
    int extension_offset;

    // Zero all of the memory for this thread.
    memset( out_file_name, '\0', 64 );
    for (i = 0; i < NEVENTS; i++ ) {
        event_info[i].filename = NULL;
        event_info[i].line_number = 0;
        event_info[i].count = 0;
        event_info[i].transition_ptr = NULL;
        event_info[i].reservoir_ptr = NULL;
    }

    // Initialize variables so we know we are just starting up.
    last_event_ind = -1;

    // We haven't overflowed yet.
    overflow = 0;

    // Figure out our process and thread_id
    my_pid = getpid();
    my_tid = syscall( __NR_gettid );


    // Seed the random number generator
    fast_srand( my_pid * my_tid );

    /*
     * Now we want to set up a file so we can write to it when dump_im_tracing is called.
     * It could be the case that we already have an fd, and the caller executed this function to wipe
     * our memory (as done in the unit tests). If that is the case, don't bother opening a new
     * file.
     */

    if( out_fd == -1 ) {
        /*
         * We are going to add extensions in case this pid/tid pair already has an open file. This
         * should not happen, but can if there are residual files from previous processes kicking around
         * in /tmp and we looped around on pids.
         */
        for( extension_offset = 0; ; extension_offset++ ) {
            memset( out_file_name, '\0', 64 );
            snprintf( out_file_name, 64, "/tmp/%d.%d.%d.im.out", my_pid, my_tid, extension_offset );
            out_fd = open( out_file_name, O_CREAT | O_WRONLY | O_TRUNC | O_EXCL, S_IRUSR | S_IWUSR );

            // If we got a valid return code, out_fd > 0.
            if( out_fd >= 0 ) {
                break;
            }

            /* If we received an error from open that is NOT EEXIST, it means something really
             * bad happened and we can't trace the file. Unfortunately, there isn't much we can
             * do about this problem. It seems overkill to crash a process because we couldn't trace
             * it, but writing to stdout/stderr may not work either because they may be closed or
             * redirected. Let's just print to console and hope the user notices...
             */
            if( out_fd == -1 && errno != EEXIST ) {
                printf( "WARNING: could not open file!\n" );
                break;
            }
            // EEXIST --- file already exists for PID/TID pair, bump the extension and try again.
        }
        // out_fd >= 0 or out_fd = -1 with some error.

    }

    /*
     * Some processes fork to create clones of themselves, and we will want to trace all of
     * these successfully (e.g. PostgreSQL). If we fork, we will wipe the child's memory and
     * reinitialize its tracing module. We set up a fork handler to detect this.
     *
     * Setting up a fork_handler while in a fork handler results in an infinite loop, so avoid that.
     */
    if( !in_fork_handler ) {
        pthread_atfork( NULL, NULL, im_fork );
    }
}

/* 
 * im_fork
 * If we are forked, then the child process should reset their memory and get a fd to
 * dump its tracing to.
 */
void im_fork() {
    out_fd = -1;
    in_fork_handler = 1; // We are in the fork handler, don't set up another fork handler!
    init_im_tracing();
}

/*
 * get_last_event_id()
 * Return the eventID of the most recent event
 */
int get_last_event_id() {
    return last_event_ind;
}


/*
 * get_event_hash
 * Hash the event using its (pathless)  __FILE__ and __LINE__ information
 */
uint64_t get_event_hash( const char *pathless_fname, int line_number ) {
    assert( strrchr( pathless_fname, '/' ) == NULL );
    uint64_t len = strlen( pathless_fname );
    uint64_t cur_pos = 0;
    uint64_t cur_hash = 0;

    /*
     * If there are more than 8 bytes left in the file name, interpret the bytes
     * as a uint64_t and hash it in.
     */
    while( len - cur_pos > 8 ) {
        cur_hash = cur_hash ^ (* (uint64_t *) (pathless_fname + cur_pos));
        cur_hash = rotate_left( cur_hash, 7 );
        cur_pos += 8;
    }

    /*
     * If there are more than 4 bytes left in the file name, interpret the bytes
     * as a uint32_t and hash it in.
     */
    if( len - cur_pos > 4 ) {
        cur_hash = cur_hash ^ ( * (uint32_t *) (pathless_fname + cur_pos ));
        cur_hash = rotate_left( cur_hash, 7 );
        cur_pos += 4;
    }

    /*
     * Create a uint32_t from the remaining bytes in the filename by shifting in
     * the bits, and then hash it in.
     */
    uint32_t interim = 0;
    while( len - cur_pos > 0 ) {
        uint32_t val = (uint32_t) *(pathless_fname + cur_pos);
        interim = interim | val;
        interim = interim << 8;
        cur_pos++;
    }
    cur_hash = cur_hash ^ interim;
    cur_hash = rotate_left( cur_hash, 7 );
    cur_hash ^= line_number;
    return cur_hash;
}

/*
 * is_hash_entry_for
 * Check if the provided hash is the entry for the log event corresponding to the fname and
 * line number.
 */
static _Bool is_hash_entry_for( int hash, const char *pathless_fname, int line_number ) {
    assert( strrchr( pathless_fname, '/' ) == NULL );
    return event_info[ hash ].line_number == line_number &&
        //Pretty sure we can disable the strcmp because the fname ptr should be constant for a given logline
        //TODO: Ensure that log behaviour looks about the same before/after strcmp disable on PG
        ( (void *) event_info[ hash ].filename == (void *) pathless_fname /* || strcmp( event_files[ hash ], pathless_fname ) == 0 */ );
}

/*
 * allocate this slot in the event info array
 * set up transition array and CDF ptr
 */
static void alloc_slot( int slot, const char *pathless_fname, int line_number) {
    assert( strrchr( pathless_fname, '/' ) == NULL );

    // FIXME: Is it guaranteed that the __FILE__ pointer lasts for the life of the program (presumably)?
    event_info[ slot ].filename = (char *) pathless_fname;
    event_info[ slot ].line_number = line_number;

    event_info[ slot ].transition_ptr = NULL;
    event_info[ slot ].reservoir_ptr = NULL;
}

/*
 * get_event_index()
 * Determine the id of this log line
 * Linear probe on hash collision because deletion isn't a thing
 */
int get_event_index( const char *pathless_fname, int line_number ) {
    assert( strrchr( pathless_fname, '/' ) == NULL );

    uint64_t pre_hash_id;
    int hash;
    int orig_ind_pos;

    pre_hash_id = get_event_hash( pathless_fname, line_number );
    // We need to jumble the bits around so we don't mod by line number
    // every time
    hash = pre_hash_id % NEVENTS;

    // Check hash slot
    if( event_info[ hash ].filename == NULL ) {
        // No one here, use this slot
        alloc_slot( hash, (char *) pathless_fname, line_number );
        return hash;
    }

    // Something is in the slot, check if we have a prior entry
    if( is_hash_entry_for( hash, pathless_fname, line_number ) ) {
        return hash;
    }

    // We have a hash collision, time to probe...
    orig_ind_pos = hash;

    while( ( hash = (hash + 1) % NEVENTS ) != orig_ind_pos ) {
        if( event_info[ hash ].filename == NULL ) {
            // Found an empty slot
            alloc_slot( hash,  pathless_fname, line_number );
            return hash;
        } else if( is_hash_entry_for( hash, pathless_fname, line_number ) ) {
            // Found our slot
            return hash;
        }
        //Try next slot
    }

    //Out of slots, fail
    return -1;
}

uint64_t get_current_nsec() {
    struct timespec ts;
    clock_gettime( CLOCK_REALTIME, &ts );
    uint64_t now = ts.tv_sec * NANO + ts.tv_nsec;
    return now;
}

/*
 * set_sampling_decision
 * Decides whether this thread ought the sample the next transition
 * for the given event_id. Sets should_record_transition_time
 */
int set_sampling_decision( int event_id ) {

    uint64_t event_count = event_info[ event_id ].count;
    if( event_count == 0 ) {
        should_record_transition_time = 1;
        return should_record_transition_time;
    }

    // Goes from RESERVOIR_SIZE -> 0.
    // Represents the probability of sampling
    float weight = (float) RESERVOIR_SIZE / (float) event_count;

    // Clamp fastrand() range to [0,1]
    float f = (float) fastrand() / (float) RAND_RANGE;

    // If f <= weight, then record this transition.
    if( f <= weight ) {
        should_record_transition_time = 1;
        return should_record_transition_time;
    }

    should_record_transition_time = 0;
    return should_record_transition_time;
}

static const char *remove_path_from_fname( const char *fname ) {
    const char *pos = strrchr( fname, '/' );
    if( pos != NULL ) {
        const char *pathless_fname = pos + 1; //skip the '/' char 
        return pathless_fname;
    }
    return fname;
}

/*
 * record_event()
 * Record an event for the given log line
 */
void record_event( const char *fname, int line_number ) {
    int event_id;
    char buff[128];
    int buff_len;
    int wr_thus_far;
    int wr;

    // It could be the case that the fname we are using has the fullpath, which we don't want
    const char *pathless_fname = remove_path_from_fname( fname );

    if( out_fd == -1 ) {
        //If we aren't initialized, then first do that.
        init_im_tracing();
    }

    event_id = get_event_index( pathless_fname, line_number );

    if( event_id == -1 ) {
        //Disaster, we are going to lose this event type
        //Write this out to the file, should break parsers and warn us
        overflow = 1;
        memset( buff, '\0', sizeof( buff ) );
        buff_len = snprintf( buff, 128, "ERROR: Lost event type: %s:%d!\n", pathless_fname, line_number );
        wr_thus_far = 0;
        while( wr_thus_far < buff_len ) {
            wr = write( out_fd, buff+wr_thus_far, buff_len-wr_thus_far );
            wr_thus_far += wr;
        }
        return;
    }


    event_info[ event_id ].count += 1;

    uint64_t cur_time = 0;

    /* 
     * If should_record_transition_time is set, then we know that we are sampling *this* transition time.
     * therefore, we will have set the last_recorded_time. Get the current time, subtract the last recorded
     * time from it and obtain the transition time. Update the last_recorded time to what we obtained in case
     * we want to also time the next transition.
     *
     * Note that if the should_record_transition_time is *not* set, we may still wish to record the
     * elapsed time of the next transition. To do so, we need to current time (e.g. the time of this event).
     * We'll go back and get that later based on whether we decide to sample it (set_sampling_decision).
     */
    if( last_event_ind != -1 ) {

        // TODO: Build Order-K markov model, collapse it here to Order-m where m is the minimum number
        // of important prior states for this event transition.
        TransitionCount *transition = get_relevant_transition( event_info[last_event_ind].transition_ptr, event_id );
        if( transition == NULL ) {
            transition = alloc_new_transition( &(event_info[last_event_ind]), event_id );
        }
        assert( transition != NULL );
        transition->count++;

        // If I should record the transition time, then get the current time
        // compare it to the last time I recorded and store it
        if( should_record_transition_time == 1 ) {
            cur_time = get_current_nsec();
            uint64_t last_time = last_recorded_time;
            uint64_t elapsed_nsec = 0;

            if( last_time <= cur_time ) {
                elapsed_nsec = (cur_time - last_time);
            }

            double norm_elapsed_nsec = normalize( elapsed_nsec );
            record_elapsed_ticks( last_event_ind, event_id, norm_elapsed_nsec );
        }
    }

    /*
     * N.B. We would like to sample transition times based on how often that transition occurs.
     * If we haven't observed a transition's time very often, we want more samples from it.
     * However, we can't know a priori what the upcoming transition is --- we know only what
     * the current event is. Therefore, we use the number of times we've seen the current event
     * to choose the sampling rate, assuming all transitions are equally likely. Clearly, this
     * isn't ideal. However, deciding to keep or throw away the sample later doesn't save much
     * overhead because we are already making a syscall for one timer here. Might as well make the
     * other at the end and subtract them if we are willing to tolerate that overhead.
     */

    int old_should_record_transition_time = should_record_transition_time;

    // Sampling decision applies for the next transition.
    set_sampling_decision( event_id );

    // If we should record *this* transition, but not the previous, then we need the current time.
    if( should_record_transition_time == 1 && old_should_record_transition_time == 0 ) {
        last_recorded_time = get_current_nsec();
    // If we should record now (and we did record before, then save the current timer)
    } else if( should_record_transition_time == 1 )  {
        // Store whatever time we recorded above
        last_recorded_time = cur_time;
    }
    // Otherwise, we aren't sampling the next transition

    //Update last event
    last_event_ind = event_id;
}

/*
 * get_flat_fd
 * Get an FD to write out the transition times and counts we have between a pair of events.
 */
static int get_flat_fd( const char *event_file1, int event_line1, const char *event_file2, int event_line2, pid_t my_pid, int extension_offset ) {
    char sketch_file_name[128];
    memset( sketch_file_name, '\0', sizeof( sketch_file_name ) );

    snprintf( sketch_file_name, 128, "/tmp/event-flat-%s:%d-%s:%d-%d-%d-im", event_file1, event_line1, 
        event_file2, event_line2, my_pid, extension_offset );
    out_fd = open( sketch_file_name, O_CREAT | O_WRONLY | O_TRUNC, S_IRUSR | S_IWUSR );
    if( out_fd == -1 ) {
        printf( "ERROR: could not open file: %d\n", errno );
    } 
    return out_fd;
}

static void write_reservoir_to_file( int fd, Reservoir *reservoir ) {
    char buff[512];
    for( int i = 0; i < reservoir->next_slot; i++ ) {
        int wrlen = snprintf( buff, 512, "%f\n", reservoir->value_pool[i]);
        write_to_file( fd, buff, wrlen );
    }
}

/*
 * dump_im_tracing()
 * Dump all in memory tracing information to per-thread files for offline analysis.
 */
void dump_im_tracing() {
    char buff[512];
    int i;
    int wrlen;

    // Don't dump more than once.
    if( out_fd == -2 ) {
        return;
    }

    pid_t my_pid = getpid();
    pid_t my_tid = syscall( __NR_gettid );
    for( i = 0; i < NEVENTS; i++ ) {
        if( event_info[i].filename != NULL ) {
            memset( buff, '\0', sizeof( buff ) );
            wrlen = snprintf( buff, 512, "%s:%d = %d, %ld\n", event_info[i].filename, event_info[i].line_number, i, event_info[i].count);
            write_to_file( out_fd, buff, wrlen );
        }
    }

    for( i = 0; i < NEVENTS; i++ ) {
        if( event_info[i].filename != NULL ) {
            TransitionCount *transition = event_info[i].transition_ptr;
            while( transition != NULL ) {
                memset( buff, '\0', sizeof( buff ) );
                wrlen = snprintf( buff, 512, "%d -> %d: %ld\n", i, transition->event_id, transition->count );
                write_to_file( out_fd, buff, wrlen );
                transition = transition->next;
            }
        }
    }

    close( out_fd );



    // Event Sketch
    for( i = 0; i < NEVENTS; i++ ) {
        if( event_info[i].filename != NULL ) {
            Reservoir *reservoir = event_info[i].reservoir_ptr;
            while( reservoir != NULL ) {
                out_fd = get_flat_fd( event_info[i].filename, event_info[i].line_number, event_info[reservoir->event_id].filename, event_info[ reservoir->event_id ].line_number, my_pid, my_tid );
                if( out_fd == -1 ) { 
                    reservoir = reservoir->next;
                    continue;
                }
                write_reservoir_to_file( out_fd, reservoir );
                close( out_fd );
                reservoir = reservoir->next;
            }
        }
    }

    
    out_fd = -2; // don't dump more than once.
}
