/** AceUnit test header file for package <default>.
 *
 * @warning This is a generated file. Do not edit. Your changes will be lost.
 * @file
 */

#include "AceUnit.h"

#ifdef ACEUNIT_SUITES

extern const TestSuite_t test_same_file_logFixture;

const TestSuite_t *const suitesOf1[] = {
    &test_same_file_logFixture,
    NULL
};

#if defined __cplusplus
extern
#endif
const TestSuite_t suite1 = {
    1,
#ifndef ACEUNIT_EMBEDDED
    "<default>",
#endif
    suitesOf1
};

#endif
