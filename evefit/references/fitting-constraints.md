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

- CPU: swap to a lower meta level (Compact/Enduring versions usually save CPU), use a CPU implant, fit a Small Processor Overclocking Unit rig, drop a utility module, or replace an oversized tank module with a smaller one.
- Powergrid: lower meta level, use an Auxiliary Power Core or Reactor Control Unit, drop a plate/extender, or move to a smaller weapon size.
- Calibration: use smaller rigs or replace one rig with a cheaper alternative; rigs cannot be removed partially.
- Slots/hardpoints: weapon size and count are fixed by hardpoints; utility highs and launchers compete for the same high slots.
- Drones: check bay volume, bandwidth and the number of launched drones separately; a full bay can still exceed bandwidth.

## Design order

1. Propulsion and tackle that the activity needs (AB/MWD, scram, web, point).
2. Tank sized to the incoming damage profile; resist rigs only after the buffer is adequate.
3. Damage system with ammo that applies at the intended range.
4. Utility: cap, tracking/range computers, neuts, drone link, cargo.
5. Rigs last, once CPU/PG and calibration are known.

When a fit comes from a public source, keep its purpose intact. A brawler that gains range by swapping to long-range ammo and a tracking computer is a different fit; note the change.

A rack may be left partly empty, but do it deliberately: spare highs for a probe launcher or neutralizer, spare lows for cargo expanders or a damage control. Do not leave slots empty because a module did not fit.
