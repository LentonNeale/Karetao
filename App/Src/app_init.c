#include "app_init.h"

#include "can_service.h"
#include "health_monitor.h"
#include "i2c_manager.h"
#include "joint_mapping.h"
#include "sensor_task.h"
#include "spi_slave_service.h"
#include "tca9548a_mux.h"
#include "time_service.h"

typedef struct {
    uint8_t motor_index;
    uint8_t logical_joint_id;
    uint32_t configuration_version;
    CanService_MksModel model;
    uint16_t can_id;
} App_MksMotorConfig;

/* Update this table as motors are commissioned on the CAN bus. */
static const App_MksMotorConfig s_mks_motors[] = {
    {0u, 0u, JOINT_MAPPING_SCHEMA_VERSION, CAN_SERVICE_MKS_SERVO42, 0x001u}
};

static const JointMapping_Record s_joint_mapping[] = {
    {
        .schema_version = JOINT_MAPPING_SCHEMA_VERSION,
        .logical_joint_id = 0u,
        .as5600_sensor_id = 0u,
        .motor_index = 0u,
        .can_id = 0x001u,
        .direction = 1,
        .zero_offset_mdeg = 0,
        .transmission_ratio_numerator = 1u,
        .transmission_ratio_denominator = 1u
    }
};

volatile uint32_t g_app_mks_register_failures_dbg;
volatile uint32_t g_app_lifecycle_activation_failures_dbg;
static bool s_start_requested;
static bool s_mapping_valid;

static void App_RegisterMksMotors(void)
{
    uint32_t i;

    g_app_mks_register_failures_dbg = 0u;
    for (i = 0u; i < (sizeof(s_mks_motors) / sizeof(s_mks_motors[0])); ++i) {
        if (CanService_RegisterMotor(s_mks_motors[i].motor_index,
                         s_mks_motors[i].logical_joint_id,
                         s_mks_motors[i].configuration_version,
                         s_mks_motors[i].model,
                         s_mks_motors[i].can_id) != MKS_OK) {
            g_app_mks_register_failures_dbg++;
        }
    }
}

void App_Init(void)
{
    g_app_lifecycle_activation_failures_dbg = 0u;
    s_start_requested = false;
    s_mapping_valid = JointMapping_Validate(s_joint_mapping,
                                            sizeof(s_joint_mapping) / sizeof(s_joint_mapping[0])) ==
                      JOINT_MAPPING_RESULT_OK;

    TimeService_Init();
    I2CManager_Init();
    TCA9548A_Init(TCA9548A_ADDR_0);
    SensorTask_Init();
    CanService_Init();
    if (s_mapping_valid) {
        App_RegisterMksMotors();
    } else {
        g_app_mks_register_failures_dbg++;
    }
    SpiSlaveService_Init();
    HealthMonitor_Init();
}

void App_Start(void)
{
    if (s_start_requested) {
        return;
    }

    s_start_requested = true;

    if ((I2CManager_GetLifecycleState() != LIFECYCLE_STATE_INACTIVE) ||
        (I2CManager_Activate() != LIFECYCLE_RESULT_OK)) {
        g_app_lifecycle_activation_failures_dbg++;
    }

    if (!s_mapping_valid ||
        (CanService_GetLifecycleState() != LIFECYCLE_STATE_INACTIVE) ||
        (CanService_Activate() != LIFECYCLE_RESULT_OK)) {
        g_app_lifecycle_activation_failures_dbg++;
    }

    if ((SpiSlaveService_GetLifecycleState() != LIFECYCLE_STATE_INACTIVE) ||
        (SpiSlaveService_Activate() != LIFECYCLE_RESULT_OK)) {
        g_app_lifecycle_activation_failures_dbg++;
    }

    if (!s_mapping_valid ||
        (I2CManager_GetLifecycleState() != LIFECYCLE_STATE_ACTIVE) ||
        (SensorTask_GetLifecycleState() != LIFECYCLE_STATE_INACTIVE) ||
        (SensorTask_Activate() != LIFECYCLE_RESULT_OK)) {
        g_app_lifecycle_activation_failures_dbg++;
    }
}
