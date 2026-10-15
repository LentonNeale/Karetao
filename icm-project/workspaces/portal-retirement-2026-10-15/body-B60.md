Origin: backlog story B60 (WP9, "S9.9 CI: doc_check job, lockstep cross-triggers, .map upload, -Werror on App, pinned toolchain, three warnings fixed")

## Context

CI does not run `doc_check`, does not cross-trigger when only one side of a lockstep pair changes, discards the `.map` file, lets App warnings through, and has no pinned compiler for evidence builds (findings VER-50, VER-52, VER-53, FW-27, FW-28). Three existing warnings block turning on `-Werror`.

## Scope

`.github/workflows/arm-ci.yml`, `raspberry-ci.yml` and the App compile flags. Not covered: changes to the VS Code ST bundle build, which stays development only (R28(a)).

## Acceptance Criteria

- [ ] A CI job runs `icm-project/tools/doc_check` and fails on findings
- [ ] Both workflows cross-trigger on the lockstep files (`spi_protocol.c`, `spi_payload_layout.h`, `spi_protocol.py`)
- [ ] The firmware job uploads the `.map` file alongside the ELF
- [ ] App sources build with `-Werror`, and the warnings at `i2c_manager.c:287`, `i2c_manager.c:313` and `spi_protocol.c:50` are fixed
- [ ] Ruling R28(a): CI pins the system `arm-none-eabi-gcc` used for evidence builds
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

A CI run on the branch shows the new job, the artifact and a passing build; a seeded warning fails the build.

## References

- Review findings (evidence pointers): VER-50, VER-52, VER-53, FW-27, FW-28
- Clauses: BUILD_CONTRACT Quality and Artifacts; BUILD_CONTRACT reproducibility and open decisions; CLAUDE.md "Run `icm-project/tools/doc_check` before merging a documentation change"; CLAUDE.md "When you change one side, change the other side and its tests too"; `BUILD_CONTRACT.md` "Quality and Artifacts" ("retain the ELF/map files needed for debug")
- Code and documents: `.github/workflows/`, `.github/workflows/arm-ci.yml:3-15;42-48;48-55`, `.github/workflows/raspberry-ci.yml:3-15`, `Arm_Sensor_Hub/.settings/bundles.store.json`, `Arm_Sensor_Hub/.vscode/settings.json:4-15`, `Arm_Sensor_Hub/App/Src/i2c_manager.c:287;313`, `Arm_Sensor_Hub/App/Src/spi_protocol.c:50`, `Arm_Sensor_Hub/cmake/gcc-arm-none-eabi.cmake:29;45`
- `Arm_Sensor_Hub/Documentation/BUILD_CONTRACT.md` (Quality and Artifacts; reproducibility)
