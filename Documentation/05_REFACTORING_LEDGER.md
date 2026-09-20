# Documentation Refactoring Ledger

Working memory tracking the migration of legacy `docs/project/**` content into `Documentation/**`. This ledger records the disposition of every statement and block migrated, for acceptance criterion 1 verification.

---

## WP-1: Decisions (Completed)

Pre-made decisions that block WP-2 and WP-3:

### §4.4 Residual component content
**Decision:** Option (a) — Create `Arm_Sensor_Hub/Documentation/` and `RaspberryPi_Sensor_Hub/Documentation/`.

Each component directory receives:
- A `README.md` containing the component authority declaration per `COMPONENT_DOCUMENTATION_MODEL.md` § "Component authority declaration"
- References to Karetao requirements by SYS-* identifier, never copying complete requirements
- Implementation documentation authority within the component scope

Rationale: Empties `docs/` completely while respecting authority model's component-ownership rule.

### C-1 `DATA_READY` semantics
**Decision:** Armed-then-assert model from `protocols/spi-contract.md` §8 is authoritative.

Statement: "A frame merely staged in a software buffer but not yet DMA-armed is not sufficient."

Supersedes: `firmware/CONTRACT_V1_FREEZE.md` § DATA_READY ("HIGH means a complete response frame is staged and ready for the Raspberry Pi to clock.") — this is a lower-level refinement that contradicts the freeze document's signal definition.

Source: `protocols/spi-contract.md` §8, being more specific and system-observable, takes precedence.

### C-3 SPI frame size
**Decision:** 512 bytes is the fixed transaction length; 490 bytes is the maximum payload.

Correction to migrate: `protocols/spi-contract.md` §17 currently says "512-byte maximum frame". This will be corrected to "fixed transaction frame: 512 bytes" with "maximum payload: 490 bytes" on migration to `02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md`.

Rationale: Fixed vs. maximum is a different contract for the host driver; the 512-byte framing is fixed (with DMA setup, header overhead), while payload varies.

---

## WP-2: Implementation Checklist (In Progress)

**Files to update:**
- `Documentation/06_IMPLEMENTATION_CHECKLIST.md` line 49 (component-repos-unchanged)
- `Documentation/06_IMPLEMENTATION_CHECKLIST.md` line 50 (archive exclusion)

**Reason:** Checklist must reflect final agreed scope before substantive content migration begins.

---

## Unresolved items

(none yet)

---

## Deliberately dropped statements

(none yet)

