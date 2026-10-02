# libgpiod v1.6.3 Python binding (`import gpiod`)

Source: `bindings/python/gpiodmodule.c` of libgpiod 1.6.3. Citations are identifiers in that file. Project use (`data_ready.py`): `gpiod.ChipIter()`, `chip.label`, `chip.get_line(offset)`, `line.request(consumer=, type=, flags=)`, `line.get_value()`, `line.event_wait(sec=, nsec=)`, `line.event_read()`, `line.release()`, `chip.close()`.

| Rule | Value | Citation |
|---|---|---|
| Chip constructor | The Chip object's constructor takes a description string as argument the meaning of which depends on the second, optional parameter | "gpiod_ChipType_doc" |
| Chip open modes | OPEN_BY_LABEL, OPEN_BY_NAME, OPEN_BY_NUMBER, OPEN_BY_PATH, and OPEN_LOOKUP | "gpiod_ChipType_doc" |
| Default open mode | OPEN_LOOKUP means that libgpiod should open the chip based on the best guess what the path is. This is also the default if the second argument is missing | "gpiod_ChipType_doc" |
| Chip must be closed | Callers must close the chip by calling the close() method when it's no longer used | "gpiod_ChipType_doc" |
| Chip.close | Close the associated gpiochip descriptor. The chip object must no longer be used after this method is called | "gpiod_Chip_close_doc" |
| ChipIter | Allows to iterate over all GPIO chips in the system. The ChipIter's constructor takes no arguments | "gpiod_ChipIterType_doc" |
| ChipIter ownership | Each iteration yields the next open GPIO chip handle. The caller is responsible for closing each chip | "gpiod_ChipIterType_doc" |
| Chip.label is a method | label() -> string: Get the label of the GPIO chip (registered as ml_name "label", METH_NOARGS; there is no getter named label) | "gpiod_Chip_label_doc" |
| Chip.name is a method | name() -> string: Get the name of the GPIO chip | "gpiod_Chip_name_doc" |
| Chip.num_lines | num_lines() -> integer: Get the number of lines exposed by this GPIO chip. | "gpiod_Chip_num_lines_doc" |
| Chip.get_line | get_line(offset) -> gpiod.Line object: Get the GPIO line at given offset. offset: Line offset (integer) | "gpiod_Chip_get_line_doc" |
| Line lifetime | Once the corresponding gpiod.Chip is closed, a gpiod.Line object must not be used | "gpiod_LineType_doc" |
| Line.offset is a method | offset() -> integer: Get the offset of the GPIO line. | "gpiod_Line_offset_doc" |
| Line.request signature | request(consumer[, type[, flags[, default_val]]]) -> None: Request this GPIO line | "gpiod_Line_request_doc" |
| Line.request arguments | consumer: Name of the consumer. type: Type of the request. flags: Other configuration flags. default_val: Default value of this line | "gpiod_Line_request_doc" |
| Request keyword names (LineBulk) | consumer, type, flags, default_vals | "gpiod_LineBulk_request" |
| Request default type | type = gpiod_LINE_REQ_DIR_AS_IS, flags = 0 | "gpiod_LineBulk_request" |
| Request failure | rv = gpiod_line_request_bulk(&bulk, &conf, default_vals); if (rv) return PyErr_SetFromErrno(PyExc_OSError); | "gpiod_LineBulk_request" |
| Request type constant used by project (module level) | LINE_REQ_EV_RISING_EDGE | "gpiod_ModuleConsts" |
| Other request type constants (module level) | LINE_REQ_EV_FALLING_EDGE | "gpiod_ModuleConsts" |
| Request flag constant used by project (module level) | LINE_REQ_FLAG_BIAS_DISABLE | "gpiod_ModuleConsts" |
| Other request flag constants (module level) | LINE_REQ_FLAG_BIAS_PULL_UP | "gpiod_ModuleConsts" |
| Flag bit values | gpiod_LINE_REQ_FLAG_BIAS_DISABLE = GPIOD_BIT(3); BIAS_PULL_DOWN = GPIOD_BIT(4); BIAS_PULL_UP = GPIOD_BIT(5) | "gpiod_LINE_REQ_FLAG_BIAS_DISABLE" |
| Line.get_value | get_value() -> integer: Read the current value of this GPIO line | "gpiod_Line_get_value_doc" |
| Line.event_wait signature | event_wait([sec[ ,nsec]]) -> boolean: Wait for a line event to occur on this GPIO line | "gpiod_Line_event_wait_doc" |
| event_wait arguments | sec: Number of seconds to wait before timeout. nsec: Number of nanoseconds to wait before timeout | "gpiod_Line_event_wait_doc" |
| event_wait result | Returns True if an event occurred on this line before timeout. False otherwise | "gpiod_Line_event_wait_doc" |
| event_wait keywords | kwlist = { "sec", "nsec", NULL }; parsed with "\|ll" (C longs, both default 0) | "gpiod_LineBulk_event_wait" |
| event_wait on error | if (rv < 0) return PyErr_SetFromErrno(PyExc_OSError); | "gpiod_LineBulk_event_wait" |
| Line.event_read | event_read() -> gpiod.LineEvent object: Read a single line event from this GPIO line object | "gpiod_Line_event_read_doc" |
| Line.event_read_multiple | event_read_multiple() -> list of gpiod.LineEvent object | "gpiod_Line_event_read_multiple_doc" |
| LineEvent.type | Event type of this line event (integer) | "gpiod_LineEvent_get_type_doc" |
| LineEvent constant (gpiod.LineEvent.RISING_EDGE) | RISING_EDGE | "gpiod_LineEventType" |
| Line.release | release() -> None: Release this GPIO line | "gpiod_Line_release_doc" |
| Line.is_requested | is_requested() -> boolean: Check if this user has ownership of this line | "gpiod_Line_is_requested_doc" |
| Line.set_flags | set_flags(flags) -> None: Set the flags of this GPIO line. | "gpiod_Line_set_flags_doc" |
| Version attribute | `__version__` module attribute, set from gpiod_version_string() | "__version__" |
| version_string deprecated | DEPRECATED: use __version__ module attribute instead | "gpiod_Module_version_string_doc" |
