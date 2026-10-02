# GCC ARM options the project's Cortex-M4F build uses (GCC manual, "ARM Options")

| Rule | Value | Citation |
|---|---|---|
| `-mcpu=name` sets the target processor | "GCC uses this name to derive the name of the target ARM architecture (as if specified by -march) and the ARM processor type for which to tune for performance (as if specified by -mtune)." | "3.20.5 ARM Options" |
| `cortex-m4` is a permitted `-mcpu` name | listed among the permissible names: 'cortex-m3', 'cortex-m4', 'cortex-m7' | "3.20.5 ARM Options" |
| `-mcpu` with `-march` or `-mtune` | "those options take precedence over the appropriate part of this option" | "3.20.5 ARM Options" |
| FP instructions are only used if | "-mfloat-abi is not set to 'soft'" | "3.20.5 ARM Options" |
| An `-mfpu` other than `auto` | "will override the available floating-point and SIMD extension instructions" | "3.20.5 ARM Options" |
| `fpv4-sp-d16` is a permitted `-mfpu` name | listed among: 'vfpv4-d16', 'fpv4-sp-d16', 'neon-vfpv4' | "3.20.5 ARM Options" |
| `-mfpu` default | "The setting 'auto' is the default" | "3.20.5 ARM Options" |
| `-mfpu=auto` behaviour | "It causes the compiler to select the floating-point and Advanced SIMD instructions based on the settings of -mcpu and -march." | "3.20.5 ARM Options" |
| `-mfloat-abi` permitted values | 'soft', 'softfp' and 'hard' | "3.20.5 ARM Options" |
| `-mfloat-abi=soft` | "library calls for floating-point operations" | "3.20.5 ARM Options" |
| `-mfloat-abi=softfp` | "hardware floating-point instructions, but still uses the soft-float calling conventions" | "3.20.5 ARM Options" |
| `-mfloat-abi=hard` | "generation of floating-point instructions and uses FPU-specific calling conventions" | "3.20.5 ARM Options" |
| `-mfloat-abi` default | "The default depends on the specific target configuration." | "3.20.5 ARM Options" |
| Hard-float and soft-float ABIs are not link-compatible | "you must compile your entire program with the same ABI, and link with a compatible set of libraries" | "3.20.5 ARM Options" |
