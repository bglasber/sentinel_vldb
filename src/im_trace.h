#ifndef __IM_TRACE_H__
#define __IM_TRACE_H__
#include <stdint.h>
#include <math.h>

#ifndef NEVENTS
#define NEVENTS 1024
#endif

#define RESERVOIR_SIZE 1000

/*
 * TransitionCount
 * Sorted, linked list of event transition counts
 */
struct TransitionCount;

/* TODO Right now, we can keep the transition counts between pairs of events. However,
 * in an order-k markov model, the previous k events are relevant for this transition.
 * Need to keep transition counts on this basis, and then collapse them once we have
 * enough information to gauge that the extra k states are not useful.
 */
typedef struct TransitionCount {
    int event_id;
    uint64_t count;
    struct TransitionCount *next;    
} TransitionCount;

/*
 * Reservoir
 * Sorted, linked list of reservoirs for event_ids.
 * Used to store transition times to compute CDFs.
 */
struct Reservoir;

typedef struct Reservoir {
    int event_id;
    int next_slot;
    double value_pool[RESERVOIR_SIZE];
    struct Reservoir *next;
} Reservoir;

/*
 * EventRegInfo
 * Information about a given event_id.
 * How many times an event has happened, where it comes from, etc.
 */
typedef struct EventRegInfo {
    char                *filename;
    int                 line_number;
    uint64_t            count;
    TransitionCount     *transition_ptr;
    Reservoir           *reservoir_ptr;
} EventRegInfo;

/*
 * init_im_tracing()
 * Initialize in memory tracing. When called, initializes all of the memory allocated for 
 * this thread's in memory tracing components.
 */
extern void init_im_tracing( void );

/*
 * get_overflow
 * Determine if we are out of event slots.
 */
extern int get_overflow( void );

/*
 * get_nevents()
 * Return the number of events we can track, used as bounds on the tracking arrays 
 */
extern int get_nevents( void );

/*
 * dump_im_tracing()
 * Dump all in memory tracing information to per-thread files for offline analysis.
 */
extern void dump_im_tracing( void );

/*
 * record_event()
 * Record an event for the given log line
 */
extern void record_event( const char *fname, int line_number );


/*
 * set_sampling_decision
 * Decides whether this thread ought the sample the next transition
 * for the given event_id. Sets should_record_transition_time
 */
extern int set_sampling_decision( int event_id );

/*
 * get_event_index()
 * Determine the id of this log line
 * Linear probe on hash collision because deletion isn't a thing
 */
extern int get_event_index( const char *fname, int line_number );

/*
 * get_event_reg_infos
 * Get the EventRegInfos for the current thread.
 */
extern EventRegInfo *get_event_reg_infos();

/*
 * get_last_event_id()
 * Return the eventID of the most recent event
 */
int get_last_event_id();

/*
 * get_event_hash
 * Hash the event using its __FILE__ and __LINE__ information
 */

extern uint64_t get_event_hash();

#endif
