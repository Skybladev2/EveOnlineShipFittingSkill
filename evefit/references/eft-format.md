# EFT format

EFT is the text format EVE copies to the clipboard. The importer matches English type names from the SDE.

```text
[Rifter, Armor Brawl]
200mm AutoCannon I, EMP S
200mm AutoCannon I, EMP S
200mm AutoCannon I, EMP S

1MN Afterburner I
Small Shield Extender I

Damage Control I
Micro Auxiliary Power Core I

Small Core Defense Field Extender I
Small Core Defense Field Extender I
Small Core Defense Field Extender I

Hobgoblin II x2
```

Rules:

- First line: `[Ship Name, Fit Name]`. The fit name is free text; keep it short.
- One module per line, in slot order: low slots, medium slots, high slots, rigs, subsystems, drones, cargo, implants.
- A loaded charge follows its module after a comma: `200mm AutoCannon I, EMP S`.
- Ancillary and charge-fed modules must be loaded on their own line: `Small Ancillary Armor Repairer, Nanite Repair Paste`, `Ancillary Shield Booster, Cap Booster 50`, `Small Capacitor Booster II, Cap Booster 50`. A cargo entry such as `Nanite Repair Paste x8` is spare paste for reloads; on its own it does not load the repairer, which then repairs only its unboosted amount (about one third). In practice a single ancillary repairer is not reloaded mid-fight, so the cargo line matters mainly when multiple repairers are fitted or between fights; see [matchup-scoring.md](matchup-scoring.md) for how to model it.
- Stacked items: drones and cargo use `xN` (`Warrior II x5`). Modules repeat on separate lines; some tools also accept `xN`.
- Blank lines are cosmetic but make the fit readable and help humans verify slot groups.
- Implants and cargo appear after modules and drones as plain names. Write `Zainou 'Deadeye' Trajectory Analysis TA-701`, not `Slot 1: ...`; the prefix becomes part of the item name.
- Do not add comments; the parser treats them as item names.
- T3 subsystems are listed after rigs.

Names must match the SDE exactly, including punctuation such as `200mm` versus `200mm` variants and faction prefixes (`Republic Fleet`, `Domination`). Use `evefit.py search` when unsure.

`evefit.py validate` returns a normalized EFT block that groups slots and preserves charges. Deliver that block; it is guaranteed to round-trip through EVE's importer.

## Overload placement

Heat spreads between adjacent modules in the same rack. Three categories
matter for placement:

- **Hot:** modules you will actually overload.
- **Effectively passive:** overloadable modules you will not overload because
  they already do their job. They generate no heat and can buffer two hot
  modules. A tracking disruptor whose debuff is sufficient is the usual case.
- **Truly passive:** modules the UI cannot overload. They matter only when they
  sit between hot modules; with no hot neighbor, their placement is irrelevant.

Interleave hot modules with effectively passive or truly passive modules, an
empty slot if the fitting window allows one, or the rack edge. Two hot modules
side by side heat each other; a buffer gives the overloaded module more time
before heat damage disables it.

Examples:

- If you overheat the afterburner and scrambler and the tracking disruptor is
  not being overloaded, put the TD between them: AB - TD - scrambler. The TD
  is effectively passive for heat and does not add heat of its own.
- If every module in the rack will be overheated, put the modules you must keep
  running at the edges and the most expendable or heat-tolerant module in the
  middle; do not sandwich a critical module between two modules you routinely
  overheat.
- If a rack has one hot module and several passive or effectively passive
  modules, put the hot one at an edge next to a buffer.
- A passive module with no hot neighbor has no placement work to do. In the
  current Rifter, Damage Control is not the heat source and has no hot low-slot
  neighbor, so its position is irrelevant; the TD is the effective buffer in
  the mid rack.

Reordering within a rack does not change CPU, powergrid or calibration. Run
`validate` after reordering and keep each charge on its module line. Heat
placement delays damage; it does not prevent it. Do not leave out a required
module just to create a gap.

A blank line in EFT is cosmetic. If you need an actual empty slot between two
modules in the in-game rack, say so explicitly; the EFT list itself only shows
the fitted modules in order.

Loaded ancillary example:

```text
[Rifter, Kinetic Active]
Kinetic Energized Membrane II
200mm Rolled Tungsten Compact Plates
Small Ancillary Armor Repairer, Nanite Repair Paste
Counterbalanced Compact Gyrostabilizer

1MN Afterburner II
Initiated Compact Warp Scrambler
Fleeting Compact Stasis Webifier

200mm AutoCannon II, Republic Fleet EMP S
200mm AutoCannon II, Republic Fleet EMP S
200mm AutoCannon II, Republic Fleet EMP S

Small Kinetic Armor Reinforcer I
Small Kinetic Armor Reinforcer I
Small Capacitor Control Circuit I

Nanite Repair Paste x8
```
