# libgpiod v1.6.3 core library semantics (header and NEWS)

Source: `include/gpiod.h` and `NEWS` of libgpiod 1.6.3 (the Python binding calls these functions). Citations are identifiers or phrases in those files.

| Rule | Value | Citation |
|---|---|---|
| Request type: as-is | GPIOD_LINE_REQUEST_DIRECTION_AS_IS: Request the line(s), but don't change current direction | "GPIOD_LINE_REQUEST_DIRECTION_AS_IS" |
| Request type: input | GPIOD_LINE_REQUEST_DIRECTION_INPUT: Request the line(s) for reading the GPIO line state | "GPIOD_LINE_REQUEST_DIRECTION_INPUT" |
| Request type: output | GPIOD_LINE_REQUEST_DIRECTION_OUTPUT: Request the line(s) for setting the GPIO line state | "GPIOD_LINE_REQUEST_DIRECTION_OUTPUT" |
| Request type: falling | GPIOD_LINE_REQUEST_EVENT_FALLING_EDGE: Only watch falling edge events | "GPIOD_LINE_REQUEST_EVENT_FALLING_EDGE" |
| Request type: rising | GPIOD_LINE_REQUEST_EVENT_RISING_EDGE: Only watch rising edge events | "GPIOD_LINE_REQUEST_EVENT_RISING_EDGE" |
| Request type: both | GPIOD_LINE_REQUEST_EVENT_BOTH_EDGES: Monitor both types of events | "GPIOD_LINE_REQUEST_EVENT_BOTH_EDGES" |
| Flag: bias disable | GPIOD_LINE_REQUEST_FLAG_BIAS_DISABLE: The line has neither either pull-up nor pull-down resistor | "GPIOD_LINE_REQUEST_FLAG_BIAS_DISABLE" |
| Flag: pull down | GPIOD_LINE_REQUEST_FLAG_BIAS_PULL_DOWN: The line has pull-down resistor enabled | "GPIOD_LINE_REQUEST_FLAG_BIAS_PULL_DOWN" |
| Flag: pull up | GPIOD_LINE_REQUEST_FLAG_BIAS_PULL_UP: The line has pull-up resistor enabled | "GPIOD_LINE_REQUEST_FLAG_BIAS_PULL_UP" |
| Flag: active low | GPIOD_LINE_REQUEST_FLAG_ACTIVE_LOW: The active state of the line is low (high is the default) | "GPIOD_LINE_REQUEST_FLAG_ACTIVE_LOW" |
| Bias reported | Returns GPIOD_LINE_BIAS_PULL_UP, GPIOD_LINE_BIAS_PULL_DOWN, GPIOD_LINE_BIAS_DISABLE or GPIOD_LINE_BIAS_AS_IS | "GPIOD_LINE_BIAS_AS_IS" |
| Bias as-is meaning | The internal bias state is unknown | "GPIOD_LINE_BIAS_AS_IS" |
| Event types | GPIOD_LINE_EVENT_RISING_EDGE: Rising edge event; GPIOD_LINE_EVENT_FALLING_EDGE: Falling edge event | "GPIOD_LINE_EVENT_RISING_EDGE" |
| Event timestamp | Best estimate of time of event occurrence | "Best estimate of time of event occurrence" |
| Event wait | Wait for an event on a single line | "Wait for an event on a single line" |
| Event wait return | 0 if wait timed out, -1 if an error occurred, 1 if an event occurred | "gpiod_line_event_wait" |
| Bias flags need kernel 5.5 | added support for bias flags which are a new functionality first available in linux v5.5; subsequently the library now requires v5.5 kernel headers to build | "added support for bias flags" |
| SET_CONFIG needs kernel 5.5 | added support for the new SET_CONFIG ioctl(): this too is a new functionality added in linux v5.5 | "SET_CONFIG ioctl" |
| v1.6.3 changes | fix uninitialized default_vals being passed to gpiod_LineBulk_request() in Python bindings | "libgpiod v1.6.3" |
| v1.6.1 changes | fix a crash in Line.request() when it's called without keyword arguments | "libgpiod v1.6.1" |
| v1.6 changes | add a standardized '__version__' module attribute in Python bindings | "libgpiod v1.6" |
