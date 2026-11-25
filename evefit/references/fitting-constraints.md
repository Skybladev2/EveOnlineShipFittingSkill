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

## Re-audit downgrades when headroom changes

A fitting downgrade is provisional. After any change that frees CPU, powergrid,
calibration, a slot or a hardpoint, revisit every module that was fitted only
to make the fit legal. Test the higher-meta/T2 or larger alternative in the
complete fit; do not assume it still fails because it failed in an earlier
draft.

1. Keep a list of modules with `Compact`, `Enduring`, `Restrained`, `Scoped`,
   meta 0/1, or a smaller size than the slot allows.
2. Compare the next meta/T2 version with `attrs`, including CPU, powergrid,
   calibration, speed, cap use and the actual combat stat that matters.
3. Put the candidate into the full EFT, then run `checknames` and `validate`.
4. Adopt it if it fits and improves the fit's job; otherwise record the exact
   binding constraint.
5. Recheck speed, range control, capacitor and EHP after each adopted change.

Worked example: an early Rifter draft used a 1MN Y-S8 Compact Afterburner
because CPU was tight. It was the right choice against 1MN Afterburner I:
13 vs 15 CPU, 9 vs 10 powergrid, and 125% vs 115% speed. Later swaps freed
2 tf CPU and 2 MW, and 1MN Afterburner II then fit, adding about 70 m/s for
0.3% less cap stability. The lesson is not "always use T2"; it is "re-run the
comparison after the constraints change." Check the reverse too: a higher meta
with worse cap use or fitting cost can be a downgrade for the actual plan.

Armor plates need the same audit. The 100mm Rolled Tungsten Compact and
100mm Crystalline Carbonide Restrained plates both give 250 armor; Restrained
is 2.5 t lighter for +2 tf CPU and +1 MW PG. Steel Plates II gives 300 armor
for +4 tf and +2 MW, and 2.5 t more mass. On this Rifter that is +100 EHP
(+2.9%) for -1 m/s (-0.28% of the ~357 m/s base, -0.07% of the 1,522 m/s
afterburner speed). Steel II is the better trade when the last 2 MW are not
needed elsewhere; record the zero powergrid headroom. The point is to compare
both absolute and relative deltas, not to reject a plate because a secondary
number moves slightly.

## Compare absolute and relative deltas

Every swap has two deltas:

- **Absolute:** new minus old, in the metric's own units.
- **Relative:** (new - old) / old x 100%, against the baseline that matters.

For speed, state which baseline you are using: hull base speed, afterburner
speed or webbed speed. The same -1 m/s is 0.28% of 357 m/s, but only 0.07% of
1,522 m/s. For EHP, use EHP against the actual damage profile, not a generic
omni number if the opponent's ammo is known.

Adopt a swap when the relative gain in the metric that decides the fight is
larger than the relative loss in the secondary metric, and the fit remains
legal with acceptable CPU, powergrid and calibration headroom. Do not use a
single absolute threshold, and do not judge a change by one number alone:
100 EHP is 2.9% of 3,404 EHP but 0.1% of 100,000 EHP; 10 m/s is 5% of
200 m/s but 0.2% of 5,000 m/s.

Record both deltas in the comparison, together with the fitting margins, so
the reader can see why the trade was accepted or rejected.

## Remove redundant support modules

Audit in both directions. Besides upgrading fitting-driven downgrades, remove
modules that only add margin to a condition already satisfied.

1. Identify support modules that do not change a pass/fail check: a cap rig or
   CPR when the fit is stable without it, a resist module against a damage
   type that is not incoming, or a plate on a fit that never gets hit.
2. Remove the module and validate the complete fit. If the remaining margin
   still covers the expected fight, the module was redundant.
3. Test what the freed slot buys in the metric that decides the fight: damage,
   resist, speed or application. Validate that candidate too.
4. Keep the support module only when its absence changes the outcome, not when
   it merely makes an already acceptable number look nicer.

Worked example: a Rifter with afterburner, scrambler and range-scripted TD was
82.6% cap stable without Small Capacitor Control Circuit I and 85.4% with it.
The kill took 67-95 s in both cases, so cap never bound. Replacing the CCC with
Small Projectile Burst Aerator II kept cap stable and raised DPS from 127.6 to
135.1 (+5.9%) with the same tank and speed. The cap rig was over-insurance.

## Compare complete rig sets

Rig slots are a set, not three independent upgrades. A T2 damage rig can use
the calibration that would otherwise fit two useful rigs. Distinct bonuses are
a useful default, not a requirement: when one stat is the win condition,
stacking the same bonus can be correct even after the stacking penalty.

Worked Rifter example:

- Burst Aerator II + Polycarbon I: 400 calibration, two rigs, 135.1 DPS,
  3,504 EHP vs Void/Null, 1,520 m/s.
- Burst Aerator I + Polycarbon I + Kinetic Armor Reinforcer I: 350
  calibration, three rigs, 127.6 DPS, 3,790 EHP vs Void/Null, 1,520 m/s.
- Burst Aerator I + Polycarbon I + Kinetic Armor Reinforcer II: 375
  calibration, three rigs, 127.6 DPS, 3,849 EHP. The T2 rig costs about 5.0M
  against 380k for the T1 version (13x) and adds only 59 EHP (1.5%), so it is
  rejected on a 6.6M Rifter.
- Burst Aerator I + Kinetic II + Thermal II: 350 calibration, three rigs,
  127.6 DPS, 4,431 EHP, 1,474 m/s (no Polycarbon; both T2 rigs are expensive).
- Burst Aerator I + Polycarbon I + Ancillary Current Router I: 400
  calibration, 5.2 MW powergrid headroom, no combat bonus.

The first and third sets trade 7.5 DPS (-5.5%) for 286 EHP (+8.2%) at
identical speed and cap, for one cheap T1 rig. Use the three-rig set when the
empty slot would otherwise be wasted and the extra tank covers the actual
damage profile. Use the two-rig set when damage is the binding clock. Do not
fill a slot with a redundant cap rig just to avoid an empty slot, and do not
pay 13x for a T2 rig that adds 1.5% EHP on a cheap hull.

The same-bonus option is legitimate. If the target's tank is the binding
clock, a second damage rig that adds only 4% after stacking can still beat a
resist rig that adds no TTK reduction. If survival against an alpha strike is
the binding clock, stack HP or the relevant resist even at a penalty. Compare
the next same-bonus rig after its stacking penalty with the best different-bonus
rig, and record which constraint decided the choice. A full rack is not a goal
by itself, and an empty slot is not a failure.

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
6. Whenever a swap frees resources, repeat this check for every earlier
   downgrade. A module that was necessary in the previous draft may no longer
   be necessary in this one.

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
