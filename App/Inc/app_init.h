#ifndef APP_INIT_H
#define APP_INIT_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void App_Init(void);
void App_Start(void);
uint32_t App_GetMksRegisterFailureCount(void);
uint32_t App_GetLifecycleActivationFailureCount(void);

#ifdef __cplusplus
}
#endif

#endif /* APP_INIT_H */
