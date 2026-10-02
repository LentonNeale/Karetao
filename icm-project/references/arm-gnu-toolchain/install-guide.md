# Arm GNU Toolchain install guide (learn.arm.com)

| Rule | Value | Citation |
|---|---|---|
| What the toolchain is | "Arm GNU Toolchain is a community-supported, pre-built GNU compiler toolchain for Arm-based CPUs." | "About this Install Guide" |
| Recommended for bare-metal targets such as arm-none-eabi | "This is the recommended approach for bare-metal and embedded targets such as arm-none-eabi." | "About this Install Guide" |
| Version advice | "We generally recommend the latest version" | "About this Install Guide" |
| Guide example version | "Arm GNU Toolchain version 15.2.Rel1" | "Install the Arm GNU Toolchain on Linux" |
| Linux host architectures | "Available for x86_64 and AArch64 host architectures" | "Download the Arm GNU Toolchain" |
| Linux unpack command | `tar xJf arm-gnu-toolchain-<version>-<host-arch>-<TRIPLE>.tar.xz -C /path/to/install/dir` | "Install the Arm GNU Toolchain on Linux" |
| Put the toolchain on PATH | `export PATH=/path/to/install/dir/bin:$PATH` | "Install the Arm GNU Toolchain on Linux" |
| Verify the install | `arm-none-eabi-gcc -v` | "Verify the installation" |
| Windows installer example for releases before 15.2.Rel1 | `arm-gnu-toolchain-14.3.rel1-mingw-w64-i686-arm-none-eabi.exe` | "Releases prior to 15.2.Rel1" |
| Windows installer type from 15.2.Rel1 | `.msi`, e.g. `arm-gnu-toolchain-15.2.rel1-mingw-w64-i686-arm-none-eabi.msi` | "Releases starting from 15.2.Rel1" |
| Licence | "Arm GNU Toolchain is open source software. You don't need any licenses to use it." | "Setting up product license" |
