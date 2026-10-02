# py-spidev: behaviour in spidev_module.c

Read from `spidev_module.c` on the master branch (module version below). Citations are identifiers or messages in that file.

| Rule | Value | Citation |
|---|---|---|
| Module version in file | #define _VERSION_ "3.8" | "_VERSION_" |
| xfer docstring | CS will be released and reactivated between blocks. delay specifies delay in usec between blocks. | "SpiDev_xfer_doc" |
| xfer2 docstring | Perform SPI transaction. CS will be held active between blocks. | "SpiDev_xfer2_doc" |
| List size limit constant | #define SPIDEV_MAXPATH 4096 (also the limit on list length for xfer and xfer2) | "SPIDEV_MAXPATH" |
| Over-limit error | Argument list size exceeds %d bytes. | "wrmsg_listmax" |
| Empty list error | Empty argument list. | "wrmsg_list0" |
| Non-integer element error | Non-Int/Long value in arguments: %x. | "wrmsg_val" |
| xfer2 issues one kernel message | status = ioctl(self->fd, SPI_IOC_MESSAGE(1), &xfer); with xfer.len = len | "SpiDev_xfer2" |
| xfer issues one transfer per byte | xferptr[ii].len = 1; ioctl(self->fd, SPI_IOC_MESSAGE(len), xferptr) (under `SPIDEV_SINGLE`) | "SpiDev_xfer" |
| xfer2 speed default | xfer.speed_hz = speed_hz ? speed_hz : self->max_speed_hz; | "SpiDev_xfer2" |
| xfer2 bits default | xfer.bits_per_word = bits_per_word ? bits_per_word : self->bits_per_word; | "SpiDev_xfer2" |
| Block-size control file | #define BLOCK_SIZE_CONTROL_FILE "/sys/module/spidev/parameters/bufsiz" | "BLOCK_SIZE_CONTROL_FILE" |
| xfer3 fallback block size | #define XFER3_DEFAULT_BLOCK_SIZE SPIDEV_MAXPATH | "XFER3_DEFAULT_BLOCK_SIZE" |
| xfer3 maximum block size | #define XFER3_MAX_BLOCK_SIZE 65535 | "XFER3_MAX_BLOCK_SIZE" |
| Initial attribute values | self->mode = 0; self->bits_per_word = 0; self->max_speed_hz = 0; | "SpiDev_new" |
| Open docstring | open(X,Y) will open /dev/spidev<X>.<Y> | "SpiDev_open_doc" |
| Permission remark | Because the SPI device interface is opened R/W, users of this module usually must have root permissions. | "SpiDev_module_doc" |
| read0 workaround | in CS_HIGH mode CS isn't pulled to low after transfer, but after read | "SpiDev_xfer" |
| Setting max_speed_hz | ioctl(self->fd, SPI_IOC_WR_MAX_SPEED_HZ, &max_speed_hz) | "SpiDev_set_max_speed_hz" |
