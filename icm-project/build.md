# Build and test commands

These mirror CI (`.github/workflows/arm-ci.yml`, `raspberry-ci.yml`). Directories are relative to the repo root.

To check the required tools, run `workspace/scripts/check-deps.sh`. Add `--install` to install missing apt packages; it asks before using sudo. The tool list is in `deps.txt`.

| Component | Directory | Command | Notes |
|---|---|---|---|
| Arm host tests | `Arm_Sensor_Hub` | `cmake --preset HostTests && cmake --build --preset HostTests && ctest --preset HostTests --output-on-failure` | Native build, no toolchain needed |
| Arm firmware (Debug) | `Arm_Sensor_Hub` | `cmake --preset Debug && cmake --build --preset Debug` | Needs `arm-none-eabi-gcc`; required for every firmware change |
| Arm firmware (Release) | `Arm_Sensor_Hub` | `cmake --preset Release && cmake --build --preset Release` | Required before release |
| Pi SPI tests | `.` | `python3 -m unittest discover -s RaspberryPi_Sensor_Hub/tests/spi -p 'test_*.py' -v` | Standard library only |
| Doc links | `.` | `python3 workspace/scripts/link-check.py` | Exit 1 on broken links |
