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
- Stacked items: drones and cargo use `xN` (`Warrior II x5`). Modules repeat on separate lines; some tools also accept `xN`.
- Blank lines are cosmetic but make the fit readable and help humans verify slot groups.
- Implants and cargo appear after modules and drones as plain names. Write `Zainou 'Deadeye' Trajectory Analysis TA-701`, not `Slot 1: ...`; the prefix becomes part of the item name.
- Do not add comments; the parser treats them as item names.
- T3 subsystems are listed after rigs.

Names must match the SDE exactly, including punctuation such as `200mm` versus `200mm` variants and faction prefixes (`Republic Fleet`, `Domination`). Use `evefit.py search` when unsure.

`evefit.py validate` returns a normalized EFT block that groups slots and preserves charges. Deliver that block; it is guaranteed to round-trip through EVE's importer.
