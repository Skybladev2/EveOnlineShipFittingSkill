# Matchup simulation

A matchup answer is a scenario, not a comparison of two paper-DPS numbers.
Never assume the target is stationary, unwebbed, at zero transversal, or
shooting into its best resist. Work through the points below and state the
assumptions that drive the result.

## Define the scenario

Before calculating, fix the terms that change the outcome:

- Starting range, and whether either ship is already tackled.
- Space: highsec gate, lowsec plex, nullsec bubble, wormhole; whether hostiles
  can bring backup.
- Both pilots' fits, ammo and implants; command bursts and links if any.
- Solo, small gang or fleet, and whether remote reps or logi are present.
- Skills. The skill's validation assumes all V; say so, or note the difference.

If the user did not specify, choose the most common case for the activity and
state it. Ask only when the answer would change the fit or the recommendation.

## Movement and application

Paper DPS assumes the target sits still at the weapon's optimal range. Real
application depends on geometry:

- **Range.** Check DPS at more than one band: point-blank, scram/web range,
  point range and long range. A brawler that cannot close and a kiter that
  cannot hold range both lose to their bad band.
- **Transversal and tracking.** Angular velocity is transversal speed divided
  by range. Compare it with the weapon's tracking and the target's signature
  resolution. Fast frigates orbiting a battleship at close range can reduce
  applied damage by an order of magnitude. Webs and painters improve
  application; afterburners, MWD signature bloom and halo implants worsen it.
- **Speed and tackle.** Who controls range? A scram shuts off a microwarpdrive
  and holds a brawler; a long point lets a faster ship disengage. Consider
  overheat, prop module cycles and capacitor for the prop mod.
- **Signature.** Small signature and high speed are a tank of their own.
  Compare weapon signature resolution with the target's signature radius, and
  remember shield extenders and MWDs increase it.

## Target resists and tank

Use the defender's actual resist profile, not an average:

- Pick damage types against the lowest resist hole. T2 and faction hulls often
  have a clear hole that the killmail or ship bonuses reveal.
- Separate buffer EHP from active tank. An active tank only holds while
  capacitor, modules and reps survive; a buffer tank does not care about neuts
  but cannot recover.
- Account for the defender's own projected effects and links. A tanked fit
  with a dead cap is a buffer fit.
- Against multiple attackers, total incoming DPS and the defender's ability to
  spread or mitigate it matter more than a clean one-on-one EHP comparison.

## Projected effects

Apply effects from both sides, at their real ranges:

- **Tackle and range control:** scram, disruptor, web, grappler.
- **Capacitor warfare:** neutralizers and nosferatu, which can shut down prop,
  tackle, active tank and weapons at once. Compare cap stability under the
  incoming neut.
- **Application warfare:** tracking disruptors, guidance disruptors, ECM,
  sensor dampeners and target painters.
- **Support:** remote armor/shield/hull reps, command bursts, links, logi and
  fleet bonuses. Hostile logi can make raw DPS irrelevant.
- **Damage and tank projection:** energy neutralizers, smartbombs, bubbles and
  area effects that decide whether the fight happens at all.

If the fit has no answer to a projected effect the target commonly carries,
treat that as a losing condition even when the raw numbers look good.

## Method

1. Build both fits and run `validate` so the comparison starts from legal fits.
2. Read base DPS, EHP and capacitor from the validation output.
3. Adjust damage for range, tracking and the defender's resists. Adjust the
   defender's effective tank for capacitor pressure, reps and projected
   effects.
4. Evaluate at two or three range bands and at the transversal values that are
   realistic for the matchup. Note where the advantage changes hands.
5. Report the deciding factors: range control, application, cap pressure,
   tackle, or a specific projected effect. Name the assumptions.
6. Check recent zkillboard kills of similar fits as a sanity check on what
   actually kills them. Killmails are evidence of outcomes, not proof of a
   theoretical result.

Do not present "DPS > EHP, therefore win" as a conclusion. Give the
conditions under which each ship wins, and say what the user must do in the
fight to reach those conditions.
