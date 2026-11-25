# Fitting implants and boosters on a budget

Community fits often leave out the hardwiring and booster a pilot actually
used. Treat both as part of the proposal when they make the fit easier to fly,
but keep them inside a budget tied to the ship itself.

## Price basis

Build a **base fit price** from the hull, fitted modules, rigs, drones and a
full load of charges. Use current sell prices at the hub where the user flies
(Jita 4-4, station 60003760, unless the user names another market). Price
stacks by their real count: every module, every rig, the full drone flight and
one complete ammunition load.

Exclude implants and boosters from the base. They are optional additions, and
including them in the denominator would let an expensive implant justify
itself.

Useful sources are the in-game market, Fuzzwork market aggregates
(`https://market.fuzzwork.co.uk/aggregates/?station=60003760&types=<type ids>`),
Janice and EVE Tycoon. Quote the date and hub next to the price, because the
thresholds move with the market.

## Module price sensitivity

Module upgrades follow the same absolute-and-relative logic as implants, but
without a fixed cap. For every candidate, record:

- the absolute ISK delta (new minus old);
- the price ratio (new divided by old);
- the new module's share of the base fit price.

A T2 rig at 5.0M ISK replacing a 380k T1 rig is 13x the price and about 76% of
a 6.6M Rifter; it added 59 EHP (1.5%). Keep the T1 rig. On a 500M doctrine
hull the same 5M module is 1% of the fit and may be a trivial upgrade.

As a rule of thumb, treat a single module above roughly 20-25% of the base fit
as a major purchase. Require either a pass/fail change or a clearly large
relative gain in the metric that decides the fight. Otherwise keep the cheaper
module and state both the saved ISK and the performance given up.

## CPU and powergrid implants

| Need | Implant family | Slots |
|---|---|---|
| CPU | Zainou 'Gypsy' CPU Management EE-601 through EE-606 | 6 |
| Powergrid | Inherent Implants 'Squire' Power Grid Management EG-601 through EG-606 | 6 |

Both families occupy implant slot 6, so only one can be used in a clone. Pick
the lowest grade that covers the shortfall; higher grades give more CPU or
powergrid and cost more.

Add a CPU or powergrid implant when its price is **under 20% of the base fit
price**. If several grades qualify, choose the cheapest one that makes the fit
validate. If none qualifies, recover the resources another way or accept a
module downgrade.

Rigs are the other fitting lever. Processor Overclocking Unit rigs reduce CPU
use, and Ancillary Current Router rigs raise powergrid output. Match the rig
size to the hull and remember that rigs consume calibration, so a fitting rig
can displace a tank or damage rig.

## Boosters

Boosters are consumed per dose and last for a limited time, usually 30 minutes.
Their price is per dose, so count one dose per fight or per pair of fights when
the user's activity makes that realistic.

Add a booster when one dose costs **under 10% of the base fit price**. Choose a
booster that serves the fit's role: Drop for turret damage, Crash for missile
application, Exile for armor repair, Blue Pill for shield boost, Frentix for
optimal range, X-Instinct for signature, Mindflood for capacitor. Prefer the
Synth grade when it is enough: it has no side effects, while Standard, Improved
and Strong grades cost more and can impose drawbacks.

Check the exact booster name with `evefit.py search` and read its attributes
with `evefit.py attrs`. Do not add a booster whose drawback works against the
fit, and do not add one when the user asked for a clean or cheap hull.

## Validation limits

`validate` applies hardwiring implant effects, so an implant that fixes CPU or
powergrid shows up in the result. dogma-engine does not currently apply
booster effects in the fit calculation: it accepts the item but leaves the
stats unchanged. Validate the hull with its modules, rigs, drones, charges and
implants, then describe the booster's effect separately in the answer.

Never let an implant or booster hide an invalid fit. If the fit only validates
with an implant, say so plainly; if it validates without the implant, report
the implant as an optional upgrade. Run `checknames` on the delivered block so
both the implant and booster names survive the EFT import.
