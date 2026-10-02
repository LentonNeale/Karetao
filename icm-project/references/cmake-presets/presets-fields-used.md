# CMake presets fields used by the project (cmake-presets(7))

| Rule | Value | Citation |
|---|---|---|
| Schema `version` is required; the project file sets 3 | "A required integer representing the version of the JSON schema." | "Format" |
| Version 3 was added in CMake | "Added in version 3.21." | "Versions" |
| Version 1 (configure presets) was added in CMake | "Added in version 3.19." | "Versions" |
| Version 2 (build and test presets) was added in CMake | "Added in version 3.20." | "Versions" |
| Version 3 added to configure presets | The installDir field was added; the toolchainFile field was added; binaryDir is now optional; generator is now optional | "Versions" |
| `toolchainFile` first appears in presets version | "Added in presets version 3." | "Configure Preset" |
| `toolchainFile` relative path | "If a relative path is specified, it is calculated relative to the build directory, and if not found, relative to the source directory." | "Configure Preset" |
| `toolchainFile` precedence | "This field takes precedence over any CMAKE_TOOLCHAIN_FILE value." | "Configure Preset" |
| `toolchainFile` macro expansion | "This field supports macro expansion." | "Configure Preset" |
| `hidden` preset | "If a preset is hidden, it cannot be used in the --preset argument" | "Configure Preset" |
| `hidden` presets purpose | "hidden presets are intended to be used as a base for other presets to inherit via the inherits field." | "Configure Preset" |
| `inherits` copies fields except | name, hidden, inherits, description, and displayName | "Configure Preset" |
| `inherits` conflict between several parents | "the earlier preset in the inherits array will be preferred" | "Configure Preset" |
| `generator` when omitted (version 3 and later) | "CMake will fall back to regular generator discovery procedure." | "Configure Preset" |
| `binaryDir` relative path | "If a relative path is specified, it is calculated relative to the source directory." | "Configure Preset" |
| `binaryDir` when omitted (version 3 and later) | "CMake will calculate the path using regular methods." | "Configure Preset" |
| `cacheVariables` value forms | null, a boolean, a string (supports macro expansion), or an object with type and value | "Configure Preset" |
| `${sourceDir}` | "Path to the project source directory (i.e. the same as CMAKE_SOURCE_DIR)." | "Macro Expansion" |
| `${presetName}` (macros evaluate in the using preset) | "macros are evaluated in the context of the preset being used, even if the macro is in a field that was inherited from another preset" | "Macro Expansion" |
| Build preset `configurePreset` | "The build directory is inferred from the configure preset, so the build will take place in the same binaryDir that the configuration did." | "Build Preset" |
| Test preset `configurePreset` | "The build directory is inferred from the configure preset, so tests will run in the same binaryDir that the configuration and build used." | "Test Preset" |
| `cmakeMinimumRequired` (optional root object) | "An optional object representing the minimum version of CMake needed to build this project." | "Format" |
