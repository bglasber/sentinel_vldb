#include "log.h"
#include "im_trace.h"
#include "module.h"
#include "test_same_file_log.h"
#include "header_log.h"
#include <stdio.h>
#include <pthread.h>

static int last_log_line = 0;

static void assertHaveRightCounts( int e_distinct_events, int e_observed_events ) {
    int i;
    int observed_events;
    int distinct_events;
    int nevents;
    uint64_t *counts;

    nevents = get_nevents();
    assertEqualsM( "Expected NEVENTS = 64", nevents, 64 );
    EventRegInfo *infos = get_event_reg_infos();

    observed_events = 0;
    distinct_events = 0;
    for( i = 0; i < nevents; i++ ) {
        observed_events += infos[i].count;
        if( infos[i].count != 0 ) {
            distinct_events++;
        }
    }
    assertEqualsM( "Expected different # of unique log events.", distinct_events, e_distinct_events );
    assertEqualsM( "Expected different # of log events.", observed_events, e_observed_events );
}

static void assertEventCount( int event_id, uint64_t expected_count ) {
    EventRegInfo *infos = get_event_reg_infos();
    assertEqualsM( "Expected different event count!", infos[ event_id ].count, expected_count );
}

static void assertTransitionCount( int event_id, int o_event_id, uint64_t expected_count ) {
    //Hack for tests, we know NEVENTS is 64 when testing.
    void *event_transition_counts_pre_cast;

    EventRegInfo *infos = get_event_reg_infos();
    TransitionCount *tcounts = infos[ event_id ].transition_ptr;


    while( tcounts != NULL ) {
        if( tcounts->event_id < o_event_id ) {
            tcounts = tcounts->next;
        } else if( tcounts->event_id == o_event_id ) {
            assertEqualsM( "Expected different event transition count!", tcounts->count, expected_count );
            return;
        } else {
            tcounts = NULL;
        }
    }
    if( expected_count > 0 ) {
        assertFalseM( "Could not find transition in tracker.", tcounts == NULL );
    }
}

static void test_func( int a ) {
    LOG( "test_func: %d\n", a ); last_log_line = __LINE__;
}

static void test_func2( int a, int b ) {
    LOG( "test_func2: %d, %d\n", a, b ); last_log_line = __LINE__;
}

A_Test void testSingleLog() {
    init_im_tracing();
    LOG( "Sample test msg: %d\n", 0 ); last_log_line = __LINE__;
    assertHaveRightCounts( 1, 1 );
}

A_Test void testMomentSketchStructMembership() {

    init_im_tracing(); // all go on the same line since the line number determines event_id
    EventRegInfo *infos = get_event_reg_infos();

    LOG( "test_func SampleSketchStruct: %d\n", 10 ); last_log_line = __LINE__; LOG( "test_func: SampleSketchStruct %d\n", 11 ); last_log_line = __LINE__; LOG( "test_func: SampleSketchStruct %d\n", 12 ); last_log_line = __LINE__;

    int last_event_id_prev = get_last_event_id();

    EventRegInfo *info = &(infos[last_event_id_prev]);
    assertFalseM( "EventId not found in events tracker.", info->filename == NULL );
    /*
    DataPointArray *dpa = ed->flat_data;
    assertEqualsM( "Found DPA!", dpa->next_slot_to_fill, 2 );

    last_event_id_prev =  get_last_event_id();
    LOG( "test_func SampleSketchStruct: %d\n", 13 ); last_log_line = __LINE__;
    int event_id = get_event_index( __FILE__, last_log_line );

    EventData *prev = NULL;
    EventData *cur = NULL;
    int found = find_event_tracker( &(event_data[last_event_id_prev]), event_id, &cur, &prev );
    assertEqualsM( "Event Id not found in moments_tracker", found, 1);
    
    last_event_id_prev = get_last_event_id();
    LOG( "test_func: SampleSketchStruct %d\n", 14 ); last_log_line = __LINE__;
    event_id = get_event_index( __FILE__, last_log_line );
    found = find_event_tracker( &(event_data[last_event_id_prev]), event_id, &cur, &prev );
    assertEqualsM( "Event Id not found in moments_tracker", found, 1);

    last_event_id_prev = event_id;
    LOG( "test_func: SampleSketchStruct %d\n", 15 ); last_log_line = __LINE__;
    event_id = get_event_index( __FILE__, last_log_line );
    found = find_event_tracker( &(event_data[last_event_id_prev]), event_id, &cur, &prev );
    assertEqualsM( "Event Id not found in moments_tracker", found, 1);
    */
}

A_Test void testSameLogTwice() {
    init_im_tracing();
    test_func( 0 );
    test_func( 1 );
    assertHaveRightCounts( 1, 2 );
}

A_Test void testDifferentFuncs() {
    init_im_tracing();
    test_func( 0 );
    test_func2( 1,2 );
    test_func2( 3,2 );
    assertHaveRightCounts( 2, 3 );
}

A_Test void testSingleTransition() {
    int event_id;

    init_im_tracing();
    test_func( 0 ); // line 42
    test_func( 0 ); // line 42

    assertHaveRightCounts( 1, 2 );
    //In theory, this __FILE__ ptr could be different than the one used for earlier
    //log lines, but I've never seen this happen in practice
    event_id = get_event_index( __FILE__, last_log_line );


    assertEventCount( event_id, 2 );
    assertTransitionCount( event_id, event_id, 1 );
}


A_Test void testMultiTransitions() {
    int event_id1;
    int event_id2;
    int first_line;
    int second_line;

    init_im_tracing();

    test_func( 1 );
    first_line = last_log_line;
    test_func2( 2, 3 );
    second_line = last_log_line;
    test_func( 7 );
    test_func2( 8, 1 );

    assertHaveRightCounts( 2, 4 );

    event_id1 = get_event_index( __FILE__, first_line );
    event_id2 = get_event_index( __FILE__, second_line );

    assertEventCount( event_id1, 2 );
    assertEventCount( event_id2, 2 );

    assertTransitionCount( event_id1, event_id1, 0 );
    assertTransitionCount( event_id1, event_id2, 2 );
    assertTransitionCount( event_id2, event_id1, 1 );
    assertTransitionCount( event_id2, event_id2, 0 );
}

A_Test void testHashCollision() {
    int event_id;
    int next_event_id;
    int i, j, nevents;

    init_im_tracing();

    //64 of these to trigger NEVENT = 64
    LOG( "test: %d\n", 0 ); last_log_line = __LINE__;
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );
    LOG( "test: %d\n", 0 );

    //Assert we can fit 64 messages in (NEVENTS)
    assertEqualsM( "Expected to not overflow, but did!\n", get_overflow(), 0 );
    LOG( "test: %d\n", 0 ); //can't fit, this message is dropped

    //Assert we signal overflow when it happens
    assertEqualsM( "Expected to overflow, but didn't!\n", get_overflow(), 1 );

    //Verify that the data we recorded is correct
    nevents = get_nevents();
    for( i = 0; i < nevents; i++ ) {
        event_id = get_event_index( __FILE__, last_log_line + i );
        assertEventCount( event_id, 1 );
        for( j = 0; j < nevents; j++ ) {
            next_event_id = get_event_index( __FILE__, last_log_line + j );
            assertTrueM( "Expected to not get an overflow id!\n", next_event_id != -1 );
            if( i != nevents- 1 && j == i+1 ) {
                assertTransitionCount( event_id, next_event_id, 1 );
            } else {
                assertTransitionCount( event_id, next_event_id, 0 );
            }
        }
    }
}

A_Test void testHeaderLog() {
    int event_id;
    int hdr_event_id;
    int hdr_log_line;
    char *hdr_file;

    init_im_tracing();
    LOG( "test: %d\n", 0 ); last_log_line = __LINE__;
    header_log();
    hdr_log_line = get_header_log_line();
    hdr_file = get_header_file();

    assertHaveRightCounts( 2, 2 );
    event_id = get_event_index( __FILE__, last_log_line );
    hdr_event_id = get_event_index( hdr_file, hdr_log_line );
    assertTransitionCount( event_id, hdr_event_id, 1 );
    assertTransitionCount( event_id, (hdr_event_id + 1) % 64, 0 ); //Permute this a bit, keep it in range
}

A_Test void testMultiFileLog() {
    init_im_tracing();
    int ofile_ll1;
    int ofile_ll2;
    int this_file_ll1;
    int this_file_ll2;
    const char* ofile_fname;
    int hdr_log_line;
    char *hdr_file;
    int ofile_id1;
    int ofile_id2;
    int this_file_id1;
    int this_file_id2;
    int hdr_file_id;
    int i;

    ofile_func_call1( 1, 2 );
    LOG( "Test!\n", 0 ); this_file_ll1 = __LINE__;
    ofile_func_call2( 2.7 );
    LOG( "Test2!\n", 0 ); this_file_ll2 = __LINE__;
    ofile_func_call2( 2.7 );
    header_log();
    ofile_func_call2( 2.7 );
    header_log();
    ofile_func_call2( 2.7 );
    ofile_ll1 = get_ofile_log_line1();
    ofile_ll2 = get_ofile_log_line2();
    ofile_fname = get_ofile_fname();
    hdr_log_line = get_header_log_line();
    hdr_file = get_header_file();

    ofile_id1 = get_event_index( ofile_fname, ofile_ll1 );
    ofile_id2 = get_event_index( ofile_fname, ofile_ll2 );
    this_file_id1 = get_event_index( __FILE__, this_file_ll1 );
    this_file_id2 = get_event_index( __FILE__, this_file_ll2 );
    hdr_file_id = get_event_index( hdr_file, hdr_log_line );

    assertHaveRightCounts( 5, 9 );
    assertEventCount( ofile_id1, 1 );
    assertEventCount( ofile_id2, 4 );
    assertEventCount( this_file_id1, 1 );
    assertEventCount( this_file_id2, 1 );
    assertEventCount( hdr_file_id, 2 );

    //ofile_id1
    for( i = 0; i < 64; i++ ) {
        if( i != this_file_id1 ) {
            assertTransitionCount( ofile_id1, i, 0 );
        } else {
            assertTransitionCount( ofile_id1, i, 1 );
        }
    }

    //this_file_id1
    for( i = 0; i < 64; i++ ) {
        if( i != ofile_id2 ) {
            assertTransitionCount( this_file_id1, i, 0 );
        } else {
            assertTransitionCount( this_file_id1, i, 1 );
        }
    }

    //ofile_id2
    for( i = 0; i < 64; i++ ) {
        if( i == this_file_id2 ) {
            assertTransitionCount( ofile_id2, i, 1 );
        } else if( i == hdr_file_id )  {
            assertTransitionCount( ofile_id2, i, 2 );
        } else {
            assertTransitionCount( ofile_id2, i, 0 );
        }
    }

    //this_file_id2
    for( i = 0; i < 64; i++ ) {
        if( i != ofile_id2 ) {
            assertTransitionCount( this_file_id2, i, 0 );
        } else {
            assertTransitionCount( this_file_id2, i, 1 );
        }
    }

    //hdr_file_id
    for( i = 0; i < 64; i++ ) {
        if( i != ofile_id2 ) {
            assertTransitionCount( hdr_file_id, i, 0 );
        } else {
            assertTransitionCount( hdr_file_id, i, 2 );
        }
    }
}

void *worker_thread( void *args ) {
    int thr_id;
    int i;
    char *header_fname;
    int header_line;
    int header_event;
    int first_log_line;
    int second_log_line;
    int first_event_id;
    int second_event_id;
    char *this_fname;

    thr_id = * (int *) args;

    init_im_tracing();

    LOG( "I'm thread ID: %d\n", thr_id ); first_log_line = __LINE__;

    for( i = 0; i < 2 * (thr_id+1); i++ ) {
        header_log();
    }
    LOG( "Doing another log!\n", 0 ); second_log_line = __LINE__;

    this_fname = __FILE__;

    header_fname = get_header_file();
    header_line = get_header_log_line();
    header_event = get_event_index( header_fname, header_line );

    assertEventCount( header_event, 2 * (thr_id + 1) );
    assertTransitionCount( header_event, header_event, (2 * (thr_id +1)) - 1 );

    first_event_id = get_event_index( this_fname, first_log_line );
    second_event_id = get_event_index( this_fname, second_log_line );

    assertEventCount( first_event_id, 1 );
    assertTransitionCount( first_event_id, header_event, 1 );

    assertEventCount( second_event_id, 1 );
    assertTransitionCount( header_event, second_event_id, 1 );

    dump_im_tracing();
}

#define NUM_THREADS 4

A_Test void testMultiThreadLogs() {
    pthread_t threads[NUM_THREADS];
    int thread_args[NUM_THREADS];
    int i;
    int first_log_line;
    int second_log_line;
    char *this_fname;
    int first_event_id;
    int second_event_id;

    init_im_tracing(); 

    for( i = 0; i < NUM_THREADS; i++ ) {
        thread_args[i] = i;
        LOG( "Creating thread %d!\n", i ); first_log_line = __LINE__;
        pthread_create( &threads[i], NULL, worker_thread, &thread_args[i] ); }

    for( i = 0; i < NUM_THREADS; i++ ) {
        LOG( "Joining thread %d!\n", i ); second_log_line = __LINE__;
        pthread_join( threads[i], NULL );
    }

    this_fname = __FILE__;
    first_event_id = get_event_index( this_fname, first_log_line );
    second_event_id = get_event_index( this_fname, second_log_line );

    assertEventCount( first_event_id, NUM_THREADS );
    assertEventCount( second_event_id, NUM_THREADS );

    assertTransitionCount( first_event_id, first_event_id, NUM_THREADS-1 );
    assertTransitionCount( first_event_id, second_event_id, 1 );
    assertTransitionCount( second_event_id, second_event_id, NUM_THREADS-1 );

    dump_im_tracing();    
}

A_Test void testEventHashing() {

    init_im_tracing();

    char *sample_fname = "test.c";
    int line_number = 0;
    uint64_t hash = get_event_hash( sample_fname, line_number );
    LOG( "Got hash: %ld\n", hash );


    char *sample_fname2 = "test.c\0\0";
    uint64_t hash2 = get_event_hash( sample_fname2, line_number );
    assertEqualsM( "Expected same hash code", hash, hash2 );


    char *sample_fname3 = "a.c";
    char *sample_fname4 = "b.c";
    hash = get_event_hash( sample_fname3, line_number );
    hash2 = get_event_hash( sample_fname4, line_number );
    assertNotEqualsM( "Expected different hash code!", hash, hash2 );

    hash = get_event_hash( sample_fname, line_number );
    assertNotEqualsM( "Expected different hash_code!", hash, hash2 );

    hash = get_event_hash( sample_fname4, 4 );
    assertNotEqualsM( "Expected different hash code!", hash, hash2 );

    hash2 = get_event_hash( sample_fname4, 1000 );
    assertNotEqualsM( "Expected different hash code!", hash, hash2 );
}

A_Test void testSamplingFillsReservoir() {

    init_im_tracing();

    //Spam sample a whole bunch of times, should always be 1.
    for( int i = 0; i < 100; i++ ) {
        assertTrueM( "Expected to sample event 0.", set_sampling_decision( 0 ) == 1 );
    }

    EventRegInfo *infos = get_event_reg_infos();
    infos[ 0 ].count = RESERVOIR_SIZE - 1;

    //Spam sample a whole bunch of times, should always be 1.
    for( int i = 0; i < 100; i++ ) {
        assertTrueM( "Expected to sample event 0.", set_sampling_decision( 0 ) == 1 );
    }

    // We've seen this event a lot, should not sample it.
    infos[ 0 ].count = UINT64_MAX;
    
    // We could get really lucky and pick a 0 with fastrand(), in which case we would sample it.
    bool did_not_sample = false;
    for( int i = 0; i < 100; i++ ) {
        did_not_sample = (set_sampling_decision( 0 ) == 0);
        if( did_not_sample ) {
            break;
        }
    }

    assertTrueM( "Expected to *not* sample event 0.", did_not_sample );

    // Try a different event, confirm we can still sample it.
    for( int i = 0; i < 100; i++ ) {
        assertTrueM( "Expected to sample event 1.", set_sampling_decision( 1 ) == 1 );
    }

}
