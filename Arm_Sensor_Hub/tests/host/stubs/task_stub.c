/**
 * @file task_stub.c
 * @brief Host stand-in for the FreeRTOS task critical section (see stubs/task.h).
 */

#include "task.h"

#include "../host_test_assert.h"

static unsigned s_critical_depth;
static unsigned s_critical_entries;

void HostStub_EnterCritical(void)
{
    s_critical_depth++;
    s_critical_entries++;
}

void HostStub_ExitCritical(void)
{
    assert(s_critical_depth > 0u);
    s_critical_depth--;
}

unsigned HostStub_CriticalDepth(void) { return s_critical_depth; }
unsigned HostStub_CriticalEntryCount(void) { return s_critical_entries; }
