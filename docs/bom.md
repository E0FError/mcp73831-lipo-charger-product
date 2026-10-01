# Bill of materials & component rationale

Group 11 — **DTU LiPo Charger v1.0**, single-cell Li-Ion/LiPo charger (MCP73831).

| Ref | Value | Part / footprint | Description | Why this part |
|---|---|---|---|---|
| U1 | — | **MCP73831-2ACI/MC** (2×3 DFN) | Mini single-cell Li-Ion/LiPo charge-management controller | Programmable 15–500 mA, 4.2 V regulation, thermal regulation, reverse-discharge protection and an open-drain status output in a tiny DFN |
| C1 | 4.7 µF | MLCC (0603) | Input decoupling on VDD | Datasheet-recommended input capacitance for the linear charger |
| C2 | 4.7 µF | MLCC (0603) | Battery/output decoupling on VBAT | Datasheet-recommended output capacitance; stabilises the regulation loop |
| CR1 | SMAJ5.0A | TVS diode | Input ESD / overvoltage protection | Clamps transients on the exposed USB 5 V rail (5 V standoff) |
| D1 | — | **Dialight 598-8110-107F** (0805) | Red status LED on `STAT` | Single-LED charge-state indication per the datasheet |
| R3 | 0603 | Chip resistor | `STAT` LED series resistor | Limits LED current; value to be chosen for the desired brightness (≈1 kΩ typical) |
| R1, R2 | 5.1 kΩ | Chip resistor (0603) | USB-C CC1/CC2 pull-downs | Required so a USB-C source recognises the board as a sink and applies 5 V |
| R4 | 10 kΩ | Chip resistor (0603) | `R_PROG` preset, DIP 1 | Sets 100 mA |
| R5 | 5.1 kΩ | Chip resistor (0603) | `R_PROG` preset, DIP 2 | Sets 196 mA (E-series rounding of 200 mA) |
| R6 | 3.3 kΩ | Chip resistor (0603) | `R_PROG` preset, DIP 3 | Sets 303 mA |
| R7 | 2.4 kΩ | Chip resistor (0603) | `R_PROG` preset, DIP 4 | Sets 417 mA |
| R8 | 2.0 kΩ | Chip resistor (0603) | `R_PROG` preset, DIP 5 | Sets 500 mA (IC maximum) |
| R9 | user | `DIN0402` PTH resistor | Custom `R_PROG` (DIP 6) | Lets a user solder any resistor: `R_PROG[kΩ] = 1000 / I_REG[mA]` |
| SW1 | — | **Omron A6H-6101** | 6-position DIP switch | Selects exactly one preset resistor (or the custom one) |
| J1 | — | **JST `B2B-XH-A`** (XH, 2.5 mm) | JST battery connector | Standard hobby-battery connector; BAT+ / BAT− labelled |
| J2 | — | **Samtec `TMM-102-03-X-S`** | 2-pin PTH battery header | Alternate battery connection for users without a JST lead |
| J_input | — | **Samtec `TMM-102-03-X-S`** | 2-pin PTH 5 V input header | Power the board without a USB cable |
| USB | — | **CUI `UJC-HP-3-SMT-TR`** | USB Type-C receptacle | Primary 5 V input; USB-C replaces the specified Micro-USB for usability |

Footprints and symbols are included in `hardware/LiPo_Charger.SchLib` and
`hardware/LiPo_Charger.PcbLib`.

### Notes

- The five preset resistors implement the required 100 / 200 / 300 / 400 /
  500 mA settings using standard E-series values; the resulting currents and
  deviations are tabulated in the README and `docs/design-notes.md`.
- `R9` (DIP 6) is deliberately a **through-hole** footprint so an end user can
  fit a custom resistor without SMD rework.
- Only one battery connector should be populated/used at a time — using both
  places the cells in parallel, which the product does not support.
