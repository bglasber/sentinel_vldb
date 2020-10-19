/** AceUnit test header file for fixture test_same_file_log.
 *
 * You may wonder why this is a header file and yet generates program elements.
 * This allows you to declare test methods as static.
 *
 * @warning This is a generated file. Do not edit. Your changes will be lost.
 * @file
 */

#ifndef _TEST_SAME_FILE_LOG_H
/** Include shield to protect this header file from being included more than once. */
#define _TEST_SAME_FILE_LOG_H

/** The id of this fixture. */
#define A_FIXTURE_ID 1

#include "AceUnit.h"

/* The prototypes are here to be able to include this header file at the beginning of the test file instead of at the end. */
A_Test void testSingleLog();
A_Test void testMomentSketchStructMembership();
A_Test void testSameLogTwice();
A_Test void testDifferentFuncs();
A_Test void testSingleTransition();
A_Test void testMultiTransitions();
A_Test void testHashCollision();
A_Test void testHeaderLog();
A_Test void testMultiFileLog();
A_Test void testMultiThreadLogs();
A_Test void testEventHashing();
A_Test void testSamplingFillsReservoir();

/** The test case ids of this fixture. */
static const TestCaseId_t testIds[] = {
     2, /* testSingleLog */
     3, /* testMomentSketchStructMembership */
     4, /* testSameLogTwice */
     5, /* testDifferentFuncs */
     6, /* testSingleTransition */
     7, /* testMultiTransitions */
     8, /* testHashCollision */
     9, /* testHeaderLog */
    10, /* testMultiFileLog */
    11, /* testMultiThreadLogs */
    12, /* testEventHashing */
    13, /* testSamplingFillsReservoir */
};

#ifndef ACEUNIT_EMBEDDED
/** The test names of this fixture. */
static const char *const testNames[] = {
    "testSingleLog",
    "testMomentSketchStructMembership",
    "testSameLogTwice",
    "testDifferentFuncs",
    "testSingleTransition",
    "testMultiTransitions",
    "testHashCollision",
    "testHeaderLog",
    "testMultiFileLog",
    "testMultiThreadLogs",
    "testEventHashing",
    "testSamplingFillsReservoir",
};
#endif

#ifdef ACEUNIT_LOOP
/** The loops of this fixture. */
static const aceunit_loop_t loops[] = {
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
};
#endif

#ifdef ACEUNIT_GROUP
/** The groups of this fixture. */
static const AceGroupId_t groups[] = {
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
};
#endif

#ifdef ACEUNIT_PARAMETRIZED
/* Parameter data for parametrized methods follows. */
/** The parameter pointers of this fixture. */
static const void * const * parameters[] = {
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
};
/** The parameter sizes of this fixture. */
static const size_t parameterSizes[] = {
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
};
#endif

/** The test cases of this fixture. */
static const testMethod_t testCases[] = {
    testSingleLog,
    testMomentSketchStructMembership,
    testSameLogTwice,
    testDifferentFuncs,
    testSingleTransition,
    testMultiTransitions,
    testHashCollision,
    testHeaderLog,
    testMultiFileLog,
    testMultiThreadLogs,
    testEventHashing,
    testSamplingFillsReservoir,
    NULL
};

/** The before methods of this fixture. */
static const testMethod_t before[] = {
    NULL
};

/** The after methods of this fixture. */
static const testMethod_t after[] = {
    NULL
};

/** The beforeClass methods of this fixture. */
static const testMethod_t beforeClass[] = {
    NULL
};

/** The afterClass methods of this fixture. */
static const testMethod_t afterClass[] = {
    NULL
};

/** This fixture. */
#if defined __cplusplus
extern
#endif
const TestFixture_t test_same_file_logFixture = {
    1,
#ifndef ACEUNIT_EMBEDDED
    "test_same_file_log",
#endif
#ifdef ACEUNIT_SUITES
    NULL,
#endif
    testIds,
#ifndef ACEUNIT_EMBEDDED
    testNames,
#endif
#ifdef ACEUNIT_LOOP
    loops,
#endif
#ifdef ACEUNIT_GROUP
    groups,
#endif
#ifdef ACEUNIT_PARAMETRIZED
    parameters,
#endif
    testCases,
    before,
    after,
    beforeClass,
    afterClass
};

#endif /* _TEST_SAME_FILE_LOG_H */
