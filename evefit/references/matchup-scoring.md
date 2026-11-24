# Scoring a matchup

A matchup is decided by three clocks and a price, not by paper EHP or paper DPS.

1. **Time to kill (TTK).** Effective HP of the target under the damage types you
   actually apply, divided by your applied DPS at the real range and transversal.
2. **Time to die (TTD).** Your effective HP under the target's actual damage,
   including any repair that runs, divided by its applied DPS.
3. **Capacitor endurance.** Seconds until your capacitor empties with every
   active module running. When it empties, every cap-fed module stops at once:
   hardener, repairer, scram, web, prop. Compare it with TTK and TTD.
4. **Price.** Compare performance per ISK, not absolute performance.

Win condition: `TTK < TTD` and `TTK < capacitor endurance`, with margin for
piloting error. State the margin.

## Capacitor stability is optional

Cap-stable is convenient, not required. A fit that runs dry in 250 seconds is
fine if it kills in 100. Report the endurance seconds and what shuts off, and
prefer a fit whose endurance covers the worst-case TTK (for example against a
tankier variant of the target).

`validate` prints the stable percentage; an unstable fit prints no cap line.
The engine also exposes `capacitorDepletesIn` (negative when stable), which is
the number to quote for an unstable fit.

## Adaptive hardeners

A Reactive Armor Hardener is reported statically by most tools as a 15%
hardener. Against a locked damage type it settles much higher. Validate with:

```bash
python3 scripts/evefit.py validate fit.eft --profile kinetic
```

The engine sets `environment.reactive_armor = damage_profile` and settles the
module over its cycles; the printed EHP is then the adapted one. It takes about
ten cycles (roughly 100 seconds) to settle, so the first hundred seconds of the
fight sit between the static and adapted values. Check that the buffer covers
that ramp.

If the opponent can mix damage types, the hardener settles somewhere worse;
treat the locked-type result as a best case.

## Turret application depends on orbit

Hit chance for a turret:

```
chance = 0.5 ^ ( (angular * sig_resolution / (tracking * target_sig)) ^ 2
                 + (max(0, range - optimal) / falloff) ^ 2 )
```

with `angular = transversal / range`. For an orbiting ship the transversal is
close to its own speed; the target's motion adds or subtracts.

Use the real orbit radius, not the configured one. A pilot requests an orbit
and the ship settles wider; the gap depends on hull and propulsion mode:

| Hull | Propulsion | Real orbit offset |
|---|---|---|
| T1 and navy frigates | 1MN afterburner | about +1000 m |
| T1 and navy frigates | 5MN microwarpdrive | about +3000 m |
| Other hulls | any | smaller, exact figure unknown |

Those frigate figures are the working numbers to use. For other hulls, do not
invent an offset: run the sweep across a plausible band and report the result
as sensitive to the offset, or ask the user if the answer changes at the band
edges. `hit --prop ab` and `hit --prop mwd` apply the frigate figures; `--offset`
overrides them with a user-supplied number.

Take the gun and ship numbers from the fit itself (`hit --fit fit.eft`): the
engine gives all-V tracking, optimal range with the loaded ammo, falloff, max
velocity and DPS. A turret's base SDE tracking and optimal omit skills and ammo;
using them understates hit chance by tens of percent and pushes the
recommendation to a worse orbit. Orbiting does not hold full straight-line
speed, so treat the computed hit chance as slightly pessimistic, and add the
target's own transversal when it is not webbed down.

Procedure:

1. For each nominal orbit you consider, compute the real radius through the
   offset above.
2. Sweep nominal radii in 500 m steps over the useful band.
3. For each radius, compute hit chance and applied DPS (`DPS * chance`).
4. Compute TTK against each target variant at that radius.
5. Pick the radius that minimises TTK while staying inside your tackle
   (web, scram) and inside falloff; check the result is robust to the target's
   own movement.
6. Tell the user the **configured** orbit, converting back through the offset,
   and state the offset you assumed.

Wider is not always better: angular velocity falls with range, but once the
range term in the falloff grows the hit chance falls again. The optimum is
usually inside optimal + one falloff.

## Repair: burst versus sustained

- Ancillary armour repairer (SAAR): about 3x repair for its eight paste cycles
  (about 36 seconds at all V), then about one third. Excellent for a short
  brawl; it must be loaded with paste on the module line (`Small Ancillary
  Armor Repairer, Nanite Repair Paste`), otherwise it repairs at the unboosted
  rate from the start.
- **Single SAAR: assume no reload.** Pilots rarely reload one ancillary
  repairer mid-fight. After the eighth cycle it keeps firing unboosted, so the
  realistic profile is a 36 second burst followed by the sustained unboosted
  rate for the rest of the fight; spare paste in cargo is for between fights.
  A simulation that assumes a continuous boosted rate overstates repair badly.
- **Multiple armour repairers: assume the ancillary is reloaded.** When other
  repairers cover the gap, the ancillary one is reloaded (about 10 seconds,
  consuming another clip of paste) and the boosted phase repeats. Budget cargo
  paste per reload and count the reload time as unboosted repair from the other
  modules.
- **Ancillary shield boosters: assume reloads, staggered.** Pilots always
  reload ASBs, but multiple fitted ASBs are rarely fired together. They are
  usually run in rotation: one boosts while another reloads, giving nearly
  continuous boosted repair. Model that rotation, and count the cap booster
  charges per reload.
- Plain armour repairer (SAR): lower burst, but it runs as long as the
  capacitor does. With a capacitor power relay and repair rig it can hold a
  steady fight for minutes.
- Compare them as "repair HP/s x seconds available", not as a single EHP
  number. A sustained 24 HP/s for 250 seconds repairs more over a two minute
  fight than a 35 HP/s ancillary burst that lasts 36 seconds and then drops to
  12 HP/s.

## Cheap hardwirings and boosters

When the user allows them, include the cheap ones in the search: tracking
(MR-701), damage (SS-901), capacitor capacity and recharge (EM-8xx, EO-6xx),
armour repair amount (Hardshell TB3), signature (X-Instinct) and speed or
tracking (Drop). Price them, state the share of the fit, and remember boosters
are one dose per 30 minutes. Side-effect chance applies to Standard and stronger
grades; Synth has none.

## Worked example: Rifter versus a kinetic-locked Flycatcher

The first answer built a passive kinetic buffer: Damage Control, Kinetic Armor
Hardener, plate, kinetic rigs. It validated and won against Rage rockets only.

The better fit used a Reactive Armor Hardener plus a plain Small Armor
Repairer II, a capacitor power relay and repair rig. Statically it looked
weaker (2,621 EHP); with `--profile kinetic` the hardener settled at 0.1085
armour kinetic resonance for 6,777 kinetic EHP. The plain repairer held 24.2
HP/s for 247 seconds, so the fit won both ammo cases and cost less. The orbit
mattered too. With all-V numbers read from the fit (`hit --fit`), the Rifter
does 0.4215 rad/s tracking, 750 m optimal, 9,675 m falloff and 1,139 m/s, so the
1,000 m contact orbit lands at 2,000 m with about 0.72 hit chance and a 121
second kill. Pushing the contact orbit to 2,500 m (real 3,500 m) lifts hit
chance to 0.85 and the kill comes in near 102 seconds, against 247 seconds of
capacitor. A 500 m orbit is the worst case: 153 seconds, still inside the
capacitor but with much less margin. Base SDE tracking and optimal without
skills had predicted far worse application, which is why the sweep now reads
the calculated fit.

Lessons: score TTK/TTD, use the damage profile for adaptive hardeners, sweep
the orbit, and compare repair types by sustained output rather than burst EHP.
