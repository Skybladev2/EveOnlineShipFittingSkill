# Fitting constraints and recovery tactics

`evefit.py validate` checks the fit after skills and module effects:

- CPU, powergrid and calibration usage against the hull.
- High/medium/low/rig/subsystem/service slots, plus turret and launcher hardpoints.
- Drone bay, drone bandwidth and launched drones; fighter bay and tubes.
- Charge group and charge size for every loaded weapon.
- Rig size and ship restrictions.
- Required skills (all are assumed at V, so a failure means the hull or module is not usable this way).

Common SDE attribute IDs for drafting:

| Attribute | ID | Meaning |
|---|---|---|
| cpu | 48 | ship CPU output (tf) |
| powerOutput | 11 | ship powergrid output (MW) |
| upgradeCapacity | 1132 | calibration capacity |
| upgradeSlotsLeft | 1154 | calibration slots |
| hiSlots / medSlots / lowSlots | 14 / 13 / 12 | slot racks |
| rigSlots | 1137 | rig slots |
| turretSlotsLeft / launcherSlotsLeft | 102 / 101 | weapon hardpoints |
| droneCapacity / droneBandwidth | 283 / 1271 | drone bay and bandwidth |
| rigSize | 1547 | 1 small, 2 medium, 3 large, 4 capital |
| metaLevelOld | 633 | module meta level |
| techLevel | 422 | tech level |
| cpu (module) / power (module) | 50 / 30 | module resource usage |
| chargeSize | 128 | 1 small, 2 medium, 3 large, 4 capital |
| requiredSkillN / Level | 182+ / 277+ | skill requirements |

## Recovering resources

- CPU: swap to a lower meta level (Compact/Enduring versions usually save CPU), fit a Processor Overclocking Unit rig, use a Zainou 'Gypsy' CPU Management implant, drop a utility module, or replace an oversized tank module with a smaller one.
- Powergrid: lower meta level, fit an Ancillary Current Router rig, use an Inherent Implants 'Squire' Power Grid Management implant, use a Micro Auxiliary Power Core or Reactor Control Unit, drop a plate/extender, or move to a smaller weapon size.
- Implant slot: the CPU and powergrid hardwirings both use slot 6, so a fit cannot use both. Pick the one that covers the larger shortfall.
- Price check: add a fitting implant only when it costs under 20% of the base fit price, and a booster only when a dose costs under 10%; see [budget-implants-boosters.md](budget-implants-boosters.md).
- Calibration: use smaller rigs or replace one rig with a cheaper alternative; rigs cannot be removed partially.
- Slots/hardpoints: weapon size and count are fixed by hardpoints; utility highs and launchers compete for the same high slots.
- Drones: check bay volume, bandwidth and the number of launched drones separately; a full bay can still exceed bandwidth.

## Validate swaps; do not estimate them

A module swap is a property of the complete fit, not of the module in isolation.
Skill bonuses, rig drawbacks, implant effects and rounding can make a candidate
fit that a rough CPU or powergrid calculation rejects, or reject one that looks
close enough. When considering a higher-DPS turret, launcher, hardener,
propulsion module or rig:

1. Put the swap into the complete EFT text.
2. Run `checknames` and `validate` on that complete candidate.
3. Record used/available CPU, powergrid and calibration, plus any violation.
4. If the candidate is rejected, keep the exact binding constraint in the
   comparison instead of saying it "looks too tight."
5. If the chosen fit is legal but has very little headroom, report the exact
   margin (for example 0.3 tf CPU free) and name a fallback for pilots who
   change metas or use lower fitting skills.

Do not stop at the first legal fit when a higher-DPS or cheaper variant also
validates. The comparison should include that variant, even when another fit
wins on tank, range control or price; add a capacitor variant only when cap endurance binds.

## Design order

1. Propulsion and tackle that the activity needs (AB/MWD, scram, web, point).
2. Tank sized to the incoming damage profile; resist rigs only after the buffer is adequate.
3. Damage system with ammo that applies at the intended range.
4. Utility: cap, tracking/range computers, neuts, drone link, cargo.
5. Rigs last, once CPU/PG and calibration are known.

When a fit comes from a public source, keep its purpose intact. A brawler that gains range by swapping to long-range ammo and a tracking computer is a different fit; note the change.

A rack may be left partly empty, but do it deliberately: spare highs for a probe launcher or neutralizer, spare lows for cargo expanders or a damage control. Do not leave slots empty because a module did not fit.
