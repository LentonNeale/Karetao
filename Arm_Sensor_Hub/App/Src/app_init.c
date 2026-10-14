/**
 * @file app_init.c
 * @brief Implements the app init module.
 */

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
    {0u, 0u, JOINT_MAPPING_SCHEMA_VERSION, CAN_SERVICE_MKS_SERVO57, 0x001u}
};

/*
 * Commissioned sensor topology, confirmed 2026-09-17.
 *
 * Index is the logical axis; the value is the TCA9548A channel carrying that
 * axis AS5600, so logical joint N reads breakout pad SDN+2. Channel SD0 carries
 * a bench test sensor and is deliberately excluded from the published axes;
 * SD1 is unpopulated. Rewiring the arm means editing only this table.
 */
static const uint8_t s_sensor_mux_channels[SENSOR_TASK_AXIS_COUNT] = {
    2u,  /* 0 Joint X */
    3u,  /* 1 Joint Y */
    4u,  /* 2 Joint Z */
    5u,  /* 3 Wrist Joint 1 */
    6u,  /* 4 Wrist Joint 2 (differential motor 1) */
    7u   /* 5 Wrist Joint 3 (differential motor 2) */
};

/*
 * Encoder-fitted table, commissioning facts 2026-10-04 and 2026-10-15 (Lenton Neale). It must
 * match SYSTEM_CONFIGURATION.md section 2.1. An unfitted axis is never read and
 * is reported NOT_FITTED, not as a fault. Axes 4 and 5 are raw motor-shaft angles.
 */
static const bool s_sensor_encoder_fitted[SENSOR_TASK_AXIS_COUNT] = {
    false,  /* 0 Joint X: sensor on hand, not fitted */
    true,   /* 1 Joint Y */
    true,   /* 2 Joint Z */
    false,  /* 3 Wrist Joint 1 */
    true,   /* 4 Wrist Joint 2 (differential motor 1) */
    true    /* 5 Wrist Joint 3 (differential motor 2) */
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
volatile uint32_t g_app_sensor_configure_failures_dbg;
static bool s_start_requested;
static bool s_mapping_valid;
static bool s_sensor_channels_valid;

/**
 * @brief Executes register mks motors.
 */
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

/**
 * @brief Executes app init.
 */
void App_Init(void)
{
    g_app_lifecycle_activation_failures_dbg = 0u;
    g_app_sensor_configure_failures_dbg = 0u;
    s_start_requested = false;
    s_sensor_channels_valid = false;
    s_mapping_valid = JointMapping_Validate(s_joint_mapping,
                                            sizeof(s_joint_mapping) / sizeof(s_joint_mapping[0])) ==
                      JOINT_MAPPING_RESULT_OK;

    TimeService_Init();
    I2CManager_Init();
    TCA9548A_Init(TCA9548A_ADDR_0);
    SensorTask_Init();
    s_sensor_channels_valid =
        SensorTask_ConfigureMuxChannels(s_sensor_mux_channels,
                                        sizeof(s_sensor_mux_channels) / sizeof(s_sensor_mux_channels[0]));
    if (!s_sensor_channels_valid) {
        g_app_sensor_configure_failures_dbg++;
    }
    if (!SensorTask_ConfigureFittedAxes(s_sensor_encoder_fitted,
                                        sizeof(s_sensor_encoder_fitted) / sizeof(s_sensor_encoder_fitted[0]))) {
        g_app_sensor_configure_failures_dbg++;
        s_sensor_channels_valid = false;
    }
    CanService_Init();
    if (s_mapping_valid) {
        App_RegisterMksMotors();
    } else {
        g_app_mks_register_failures_dbg++;
    }
    SpiSlaveService_Init();
    HealthMonitor_Init();
}

/**
 * @brief Executes app start.
 */
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
        !s_sensor_channels_valid ||
        (I2CManager_GetLifecycleState() != LIFECYCLE_STATE_ACTIVE) ||
        (SensorTask_GetLifecycleState() != LIFECYCLE_STATE_INACTIVE) ||
        (SensorTask_Activate() != LIFECYCLE_RESULT_OK)) {
        g_app_lifecycle_activation_failures_dbg++;
    }
}

uint32_t App_GetMksRegisterFailureCount(void)
{
    return g_app_mks_register_failures_dbg;
}

uint32_t App_GetLifecycleActivationFailureCount(void)
{
    return g_app_lifecycle_activation_failures_dbg;
}

uint32_t App_GetSensorConfigureFailureCount(void)
{
    return g_app_sensor_configure_failures_dbg;
}
