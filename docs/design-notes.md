# Design notes — DTU LiPo Charger v1.0

Detailed reasoning behind the Group 11 single-cell Li-Ion/LiPo charger. Values
match the Altium design and `analysis/charge_current_calc.py`.

---

## 1. Product specification

| Item | Requirement | Implementation |
|---|---|---|
| Charger IC | MCP73831, 2×3 DFN | MCP73831-2ACI/MC |
| Input | 5 V from a USB port | USB-C receptacle (`UJC-HP-3-SMT-TR`) + 2-pin PTH header |
| Battery output | Two connection options | JST XH (`B2B-XH-A`) **and** 2-pin PTH header |
| Status indicator | Charging-state LED | Red 0805 LED on `STAT` |
| Charge rate | User-adjustable | 6-position DIP: 5 presets + 1 custom PTH resistor |
| Battery chemistry | Single Li-Ion/LiPo cell | 4.2 V regulation |

---

## 2. Charge-current programming

### Datasheet relation

The MCP73831 regulates the fast-charge current according to the resistor on the
`PROG` pin:

$$
I_{REG}\,[\text{mA}]=\frac{1000\ \text{V}}{R_{PROG}\,[\text{k}\Omega]}
$$

The 1000 V constant is the internal 1 V reference scaled so that 1 kΩ gives
1 mA. Rearranged for a desired current:

$$
R_{PROG}\,[\text{k}\Omega]=\frac{1000}{I_{REG}\,[\text{mA}]}
$$

### Preset selection

Targets of 100, 200, 300, 400 and 500 mA map to ideal resistors of 10, 5, 3.33,
2.5 and 2 kΩ. The nearest convenient E-series values were chosen:

| DIP | Ideal `R_PROG` | E-series fitted | Resulting `I_REG` | Deviation |
|:--:|:--:|:--:|:--:|:--:|
| 1 | 10 kΩ | **10 kΩ** | 100.0 mA | 0.0 % |
| 2 | 5 kΩ | **5.1 kΩ** | 196.1 mA | −2.0 % |
| 3 | 3.33 kΩ | **3.3 kΩ** | 303.0 mA | +1.0 % |
| 4 | 2.5 kΩ | **2.4 kΩ** | 416.7 mA | +4.2 % |
| 5 | 2 kΩ | **2.0 kΩ** | 500.0 mA | 0.0 % |
| 6 | user-defined | **PTH resistor** | custom | — |

The largest rounding effect is DIP 4 (+4.2 %), which is inside the MCP73831's
charge-current regulation tolerance and is therefore acceptable. The 500 mA
preset is also the IC's maximum programmable current.

### Custom-rate position (DIP 6)

Position 6 connects the PTH footprint `R9`, so a user can solder any resistor
to obtain a custom current using the same formula — for example 3.9 kΩ ≈
256 mA. The user guide repeats this equation so the end user can calculate the
value themselves.

---

## 3. Status LED

`STAT` is an open-drain output. With the LED tied between the 5 V rail (through
its series resistor `R3`) and `STAT`, the LED lights whenever the pin is pulled
low:

| State | `STAT` | LED | Notes |
|---|---|---|---|
| Charging | LOW | ON | Fast-charge current flowing |
| Charge complete | HIGH | OFF | Regulation reached |
| Shutdown | High-Z | OFF | Input removed / UVLO |
| No battery | HIGH | OFF | Nothing to charge |

Only a single LED is used, as recommended in the datasheet application circuit.

---

## 4. Battery chemistry compatibility

The MCP73831-2 has a **4.200 V** regulation voltage, which is the correct
full-charge voltage for a single Li-Ion/LiPo cell.

A **LiFePO₄** cell has a nominal voltage of 3.2 V and a full-charge voltage of
about 3.6 V. Charging it to 4.2 V would **overcharge** the cell, causing
permanent damage and a serious safety risk — so LiFePO₄ is explicitly not
supported. Charging more than one cell (series or parallel) is also outside the
product's capability.

---

## 5. Schematic architecture

The design uses a **hierarchical schematic** so each function stays readable:

- `Top.SchDoc` — instantiates the three functional sheets and routes the shared
  nets between them as ports (`B+`, `PROG`, `VSS`).
- `charger_IC.SchDoc` — MCP73831, `C1` (4.7 µF input), `C2` (4.7 µF battery),
  `CR1` (SMAJ5.0A TVS), `D1` (status LED) and `R3` (LED series resistor).
- `adj_current.SchDoc` — the A6H-6101 DIP switch, the five preset `R_PROG`
  resistors `R4`–`R8`, and the custom PTH resistor `R9`.
- `connect.SchDoc` — the USB-C input with its CC pull-downs, the 5 V PTH header,
  the JST battery connector and the alternate PTH battery header.

A design note on the top sheet records the convention used: *"net labels local,
ports between pages, never off-sheet."* This keeps the hierarchy clean and
avoids accidental global nets.

### Component choices (learned in class)

| Part | Choice | Reason |
|---|---|---|
| Input cap `C1` | 4.7 µF | Datasheet-recommended input decoupling for the linear charger |
| Battery cap `C2` | 4.7 µF | Datasheet-recommended output/battery decoupling |
| `CR1` | SMAJ5.0A TVS | Clamps ESD/overvoltage on the exposed USB 5 V input |
| `D1` + `R3` | Red 0805 LED + 0603 resistor | Status indication with a limiting resistor |
| USB-C CC resistors `R1`, `R2` | 5.1 kΩ each | Required pull-downs so a USB-C source supplies the sink |

> **Deviation from the brief:** the exercise specified a Micro-USB receptacle;
> the team used a **USB Type-C** receptacle instead, adding the 5.1 kΩ CC
> pull-downs so the board correctly enumerates as a sink. This is a strict
> improvement in usability and is documented here for transparency.

---

## 6. PCB layout

- **2 layers**, board outline ≈ **28.2 mm × 34.9 mm**.
- MCP73831 in the **2×3 DFN** with its **exposed pad** stitched to the ground
  plane for thermal relief.
- USB-C on an accessible board edge; JST, battery header and input header placed
  where a user can reach them.
- Silkscreen: `4.2V LiPo Battery Charger`, `USB`, `JST`, `BAT+`/`BAT−` (both
  connectors, with pin 1 marked), `5V`/`GND`, and DIP positions `1`–`6` in a
  consistent order.
- Labels sized/oriented so they remain legible in a single isometric 3D view;
  the render in the README is that verification.

---

## 7. Safety analysis (from the user guide)

| Misuse | Consequence | Guidance |
|---|---|---|
| Multiple DIP switches ON | The preset resistors are **in parallel**, so `R_PROG` drops and the charge current rises above the selected value → heat and cell stress | Use only one switch at a time |
| Battery connected to **both** JST and PTH header | Cells are in **parallel**; any state-of-charge mismatch drives large cross-currents and the charger cannot manage two cells | Connect one battery only |
| Connecting a LiFePO₄ cell | 4.2 V regulation overcharges it | Li-Ion/LiPo only |
| Choosing a very high charge rate | More heat, reduced cycle life, possible cell damage | ≈ 1 C, 2 C maximum |
| No battery connected | `STAT` stays high (LED off) — not a fault | Normal |

---

## 8. Verification / test checklist

| Check | Expected | Status |
|---|---|---|
| DIP 1 current | 100 mA | ☐ bench |
| DIP 2 current | 196 mA | ☐ bench |
| DIP 3 current | 303 mA | ☐ bench |
| DIP 4 current | 417 mA | ☐ bench |
| DIP 5 current | 500 mA | ☐ bench |
| LED while charging | ON | ☐ bench |
| LED when complete / unpowered | OFF | ☐ bench |
| USB-C enumeration | 5 V present with 5.1 kΩ CC pull-downs | ☐ bench |
| Thermal rise at 500 mA | within IC thermal regulation | ☐ bench |

*(The design is delivered as Altium sources; the bench checks above are the
recommended bring-up plan and were not part of the submission.)*

## 9. Assumptions and limitations

- Charge currents are calculated from the datasheet relation; resistor
  tolerances and the IC's regulation tolerance are not stacked in the table.
- The `R3` LED series resistor value was not recorded on the schematic
  (`Comment = R0603`); it should be chosen for the desired LED current
  (roughly 1 kΩ gives a few mA at 5 V).
- The reverse-discharge protection, thermal regulation and UVLO features are
  credited to the MCP73831 datasheet rather than measured.
- No battery-temperature (NTC/THERM) sensing is implemented; the design relies
  on the IC's internal thermal regulation.
