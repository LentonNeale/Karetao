# libgpiod Python: v1.6.3 names versus v2.3.1 names

Warning: the project uses v1 (`data_ready.py`: `gpiod.ChipIter`, `Line.event_wait`, `gpiod.LINE_REQ_EV_RISING_EDGE`). The readthedocs site documents the v2 API; code written from it will not run on v1. v1 citations are identifiers in `gpiodmodule.c` (1.6.3); v2 citations are identifiers in the Python package of libgpiod 2.3.1 (`bindings/python/gpiod/*.py`).

| v1 call (project) | v2 equivalent | Citation (v1; v2) |
|---|---|---|
| Chip(description[, how]) opens by name, label, number, path or lookup | def __init__(self, path: str): takes a path only | "gpiod_ChipType_doc"; "def __init__(self, path: str)" |
| gpiod.ChipIter() yields every chip | no ChipIter in the v2 package (checked by hand: `grep ChipIter` finds nothing); is_gpiochip_device(path) checks one path | "gpiod_ChipIterType_doc"; "def is_gpiochip_device" |
| chip.label() is a method on Chip | chip.get_info() returns ChipInfo: Immutable snapshot of a chip's status, with field label | "gpiod_Chip_label_doc"; "Immutable snapshot of a chip's status" |
| chip.get_line(offset) returns a Line | no get_line; request_lines: Request a set of lines for exclusive usage. | "gpiod_Chip_get_line_doc"; "def request_lines" |
| line.request(consumer, type, flags) | LineSettings(direction, edge_detection, bias, ...) passed in the config of request_lines | "gpiod_Line_request_doc"; "class LineSettings" |
| LINE_REQ_EV_RISING_EDGE | Edge.RISING | "gpiod_ModuleConsts"; "RISING = _ext.EDGE_RISING" |
| LINE_REQ_DIR_IN | Direction.INPUT | "gpiod_ModuleConsts"; "INPUT = _ext.DIRECTION_INPUT" |
| LINE_REQ_FLAG_BIAS_DISABLE | Bias.DISABLED (v1 says DISABLE, v2 says DISABLED) | "gpiod_ModuleConsts"; "DISABLED = _ext.BIAS_DISABLED" |
| LINE_REQ_FLAG_ACTIVE_LOW | LineSettings.active_low | "gpiod_ModuleConsts"; "active_low: bool = False" |
| line.get_value() returns an integer | def get_value(self, line: int | str) -> Value | "gpiod_Line_get_value_doc"; "def get_value" |
| line.event_wait(sec, nsec) returns a boolean | request.wait_edge_events(timeout) returns a bool, timeout a timedelta or float | "gpiod_Line_event_wait_doc"; "def wait_edge_events" |
| line.event_read() reads a single LineEvent | def read_edge_events(self, max_events: int | None = None) -> list[EdgeEvent] | "gpiod_Line_event_read_doc"; "def read_edge_events" |
| line.release() | request.release() | "gpiod_Line_release_doc"; "def release" |
| gpiod.__version__ string | api_version = _ext.api_version | "__version__"; "api_version" |
