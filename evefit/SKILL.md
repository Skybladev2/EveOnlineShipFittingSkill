---
name: evefit
description: Build, adapt, and verify EVE Online ship fits from public fit baselines (websites, EVE Frigates' Faction Warfare Yearbook, boosty.to screenshot posts, zkillboard, and YouTube descriptions, comments or on-screen fitting windows), the current official SDE, and dogma-engine, delivering a flyable EFT fit. Use when asked to create a ship fitting, improve or check a fit, compare two ships in a matchup, or explain what a hull can field.
---

# EVE Fit Builder

Deliver an EFT fit the user can paste into EVE. Start from an existing public fit when one matches the request, take current module and hull values from the official SDE, and prove the result is flyable with **all skills at level V** using EVEShip.fit's dogma-engine.

No code is trusted by default. dogma-engine ships a native extension, so it is installed and imported only after its exact wheel and the matching source tag have been reviewed and recorded. The same gate re-runs on every version, wheel or SDE change.

## Commands

Run from this skill directory.

```bash
python3 scripts/trust.py status                 # approved build, installed match, update availability
python3 scripts/trust.py prepare                # download + scan the latest engine for review
python3 scripts/trust.py approve --version V --notes "..."   # after reading the report
python3 scripts/evefit.py status                # cached and latest SDE builds, engine versions
python3 scripts/evefit.py update                # download changed tables from the latest SDE release
python3 scripts/evefit.py update --release ID   # pin a specific release (e.g. 20261120T165826Z)
python3 scripts/evefit.py env update            # refresh dogma-engine's SDE package
python3 scripts/evefit.py ship "Rifter"         # slots, CPU/PG, calibration, drones, rig size
python3 scripts/evefit.py search "500MN MWD"    # exact SDE type names
python3 scripts/evefit.py attrs "10MN AB II"    # dogma attributes and skill requirements
python3 scripts/evefit.py checknames fit.eft    # verify every item name against the SDE
python3 scripts/evefit.py validate fit.eft      # all-V calculation; exit 2 on violations
python3 scripts/evefit.py validate - < fit.eft  # read EFT from stdin
python3 scripts/evefit.py validate fit.eft --eft-only   # clean EFT block only
python3 scripts/evefit.py validate fit.eft --profile kinetic   # EHP vs one damage type; adapts a Reactive Armor Hardener
python3 scripts/evefit.py hit --fit fit.eft --target-sig 80 --target-ehp 13133 --sweep 500:3500:500 --prop ab   # all-V hit chance and TTK by orbit (ab=+1000 m, mwd=+3000 m)
```

YouTube sources:

```bash
python3 scripts/evefit.py youtube info URL --comments 40
python3 scripts/evefit.py youtube fits URL --comments 80 --out ./yt-fits
python3 scripts/evefit.py youtube frames URL --out ./yt-frames --scene 0.25 --max 18
python3 scripts/evefit.py youtube frames URL --out ./yt-frames --at 12:34
python3 scripts/evefit.py youtube frames ./local.mp4 --out ./yt-frames --interval 20
```

`validate` prints CPU, powergrid and calibration usage, EHP, DPS, capacitor stability, any rule violations, and a normalized EFT block. The first run creates a private venv under the cache directory, but installs dogma-engine only from an approved, hash-pinned wheel; with no approval it stops and points to `trust.py prepare`. YouTube commands install `yt-dlp` in that venv on first use.

## Required rules

- **Review before you run.** Never install or import dogma-engine, or any other fitting code, on trust. On the first use and on every update, run `trust.py prepare`, read the source and the scan findings, and approve the exact version. Installed files must match the approved wheel hashes. Follow [references/trust.md](references/trust.md).
- **Community fit first.** Prefer a fit the community has already vetted: a published doctrine or library fit with a stated purpose, a recent date, and repeated use. Check [references/public-fit-sources.md](references/public-fit-sources.md), including the EVE Frigate Yearbook for faction-warfare frigate and destroyer fits and tactics, and iBeast on boosty.to for recent screenshot-only fits. Then EVE YouTube; for PvP, zkillboard losses are an additional baseline. Copy a ready-to-use fit when it matches the hull, role and environment. Only when no usable fit exists, assemble one from first principles. A ready-to-use fit is a starting point, never a substitute for validation: every fit, adapted or home-made, runs through `checknames` and `validate` against the current SDE and dogma-engine before delivery.
- **General-purpose is the default brief.** Most users want a practical all-round solo, faction-warfare or small-gang fit, not a hard counter to one hull. When the user does not name an opponent or a specific environment band, build for balanced tank, damage application, range control, capacitor endurance and cost: start from community baselines and current killmail module frequency, test a band of representative opponents rather than one hull, and report where the fit wins, loses and runs out of capacitor. Exact matchup simulation still applies when the user asks for it, and the same scoring rules carry into assembly from scratch: no ideal target, no paper DPS, no static adaptive-hardener EHP.
- **YouTube order: text before images.** Read the video description and comments first; they often contain an EFT block or a corrected variant. Extract frames only when no usable text fit exists, or when the description points at a timestamp where the fit is shown. Follow [references/youtube-fits.md](references/youtube-fits.md).
- **Cite video evidence.** When a fit comes from YouTube, give the video URL and the timestamp of the description section, comment or frame. An on-screen fit must survive `checknames` and `validate` before it is delivered.
- **Frame budget.** Inspect one or two contact sheets, then re-extract only the timestamps that show the fitting window. Do not dump or view dozens of frames.
- **Ask when direction is missing.** If the purpose, environment, or role is unclear, or no public fit exists for the request, ask up to three concrete questions before locking the fit: what activity it is for, where it flies (high/low/null/wormhole, PvP or PvE), and solo or fleet with budget/tech level. Do not guess a PvP brawler when the user wanted an Abyssal runner.
- **Current values.** Query hull and module numbers from the cached SDE (`ship`, `attrs`, `search`). Do not trust remembered CPU, powergrid, calibration or slot numbers, and do not treat a video's numbers as current.
- **Validate every candidate variant, including rejected swaps.** Apply a proposed turret, launcher, tank, propulsion or rig change to the complete EFT and run `checknames` and `validate` before saying it fits or does not fit. Do not decide CPU, powergrid, calibration or slots from arithmetic or memory; skill and rig effects can change the result. If a higher-DPS or cheaper variant is rejected, record its actual violation or binding constraint. When the chosen fit has very little headroom, report the exact margin because a later meta or implant change may break it.
- **All-V proof.** Every delivered fit must pass `validate` with all skills at V. State this assumption in the answer; mention if an alpha or lower-skill variant would need changes.
- **Exact names only.** EFT import matches English SDE names. Verify each module with `search` or `checknames` before using it; a guessed meta level or faction prefix will fail.
- **Loaded charges on the module line.** Ancillary and charge-fed modules must carry their charge on the module line: `Small Ancillary Armor Repairer, Nanite Repair Paste`, `Ancillary Shield Booster, Cap Booster 50`, `Small Capacitor Booster II, Cap Booster 50`. A matching item in cargo (`Nanite Repair Paste x8`) is spare ammunition for reloads and does not load the module: a repairer imported that way runs at its unboosted amount (roughly one third of the loaded repair), which can flip a close matchup. Keep both the loaded module line and the cargo line. `validate` warns when an ancillary module has no charge.
- **zkillboard is a narrow PvP search, not a feed crawl.** The site has bot protection, so use its search feature to filter by hull, date range, region or system instead of walking the kill feed or paging through recent kills. For a PvP fit, find pilots with high efficiency in that hull (strong kill/loss ratio and ISK efficiency on recent activity), then mine those pilots' losses of the requested ship for fittings. Killmails record what a pilot lost with, so treat repeated modules across several pilots as a baseline, not one loss as a recommendation. A single killmail is a sample of one: if you call a layout common, typical, representative or dominant, give the sample window, the number of qualifying losses, and the count with that exact fit or the key modules; otherwise label it "one recent baseline." Count fitted modules and charges loaded in weapon slots, not cargo. When the user supplies the target fit, use that fit exactly and replace any inferred target. Prefer recent kills after the last balance patch, and still run `checknames` and `validate`. See [references/public-fit-sources.md](references/public-fit-sources.md).
- **Ancillary reload behaviour decides sustained repair.** A single Small Ancillary Armor Repairer is almost never reloaded in a fight: pilots burn its eight paste cycles and let it keep running unboosted, and the cargo paste is for between fights. Model one SAAR as eight boosted cycles (about 36 s) followed by the unboosted rate (roughly a third) for the rest of the engagement. When multiple armor repairers are fitted, the ancillary one is reloaded while the others repair, so model the boosted phase as renewing after the clip plus the reload while paste remains in cargo. Ancillary Shield Boosters go the other way: they are always reloaded, but multiple ASBs are rarely fired together; they are normally staggered, one boosting while another reloads, so model nearly continuous boosted reps. State which model you used; it changes sustained repair severalfold and can flip a close matchup. See [references/matchup-scoring.md](references/matchup-scoring.md).
- **Rigs and implants change CPU/PG.** When CPU or powergrid is tight, treat rigs and implants as fitting tools before downgrading modules: Processor Overclocking Unit (CPU) or Ancillary Current Router (PG) rigs, and the Zainou 'Gypsy' CPU Management or Inherent Implants 'Squire' Power Grid Management hardwirings. The two hardwirings share implant slot 6, so pick one. Rigs consume calibration. See [references/budget-implants-boosters.md](references/budget-implants-boosters.md) and [references/fitting-constraints.md](references/fitting-constraints.md).
- **Cheap fitting implants.** Price the hull, modules, rigs, drones and charges to get a base fit price; exclude implants and boosters from that total. Add a CPU or powergrid implant when its current market price is under 20% of that base. If several qualify, choose the one that fixes the actual shortfall. State the implant, its effect and its share of the base price.
- **Cheap boosters.** Add a booster that matches the fit's role when one dose costs under 10% of the same base price. Prefer the cheapest grade that gives the needed effect; Synth boosters have no side effects, while stronger grades cost more and can impose drawbacks. State the dose price and what is consumed per fight. Leave boosters out when the user rules them out.
- **Realistic matchups.** When simulating one ship against another, never assume an ideal target or perfect application. Take into account both ships' movement (speed, signature, range control and transversal), the target's actual resist profile and tank, and projected effects from either side (webs, scrams, points, neuts, ECM, damps, tracking disruptors, paints, remote reps and links). State the range, transversal and tackle assumptions behind any DPS, EHP or "who wins" claim. See [references/matchups.md](references/matchups.md).
- **Score time-to-kill against time-to-die, not buffer EHP.** For a 1v1 or anti-X fit, the objective is whether the target dies before you do and before the capacitor empties. Capacitor stability is optional; what matters is capacitor endurance versus the expected kill time, so report when the cap runs out and which modules stop with it. Keep units consistent: EHP is already resist-adjusted, so pair it with post-resist DPS; repair is raw HP/s, so convert it to effective HP or simulate raw HP. Never compute EHP divided by raw incoming DPS minus raw repair. See [references/matchup-scoring.md](references/matchup-scoring.md).
- **Adaptive hardeners need a damage profile.** A Reactive Armor Hardener shown statically is just a 15% hardener. Validate with `--profile <damage type>` (for example `--profile kinetic`) so the engine settles it toward the damage actually incoming, and account for the roughly 100 seconds it takes to settle. Never quote the static EHP for an adaptive-tank fit against a locked damage type.
- **Real orbit is wider than the configured one, and the gap depends on hull and propulsion.** A pilot sets a nominal orbit, but the ship settles wider. For T1 and navy frigates, work with roughly +1000 m when flying a 1MN afterburner and +3000 m when flying a 5MN microwarpdrive. Larger hulls drift less, but no reliable figures exist, so treat their offset as a sensitivity parameter and say so. Pass the fit with `hit --fit` so tracking, optimal, falloff, speed and DPS come from the all-V calculation; a turret's base SDE figures ignore skills and loaded ammo and understate application badly. Add `--prop ab` or `--prop mwd` for the frigate offset, or `--offset` when the user supplies a real number. Sweep configured radii in 500 m steps, convert each to its real radius, and pick the radius with the best kill time; do not apply a flat hit-chance figure. See [references/matchup-scoring.md](references/matchup-scoring.md).
- **Search the module archetypes, not one template.** Compare active and passive hardeners, plain and ancillary repairers, buffer and sustain, and the cheap hardwirings and boosters the user allows (tracking, damage, capacitor, repair). A sustained plain repairer can beat a burst ancillary one; a cheaper fit can beat an expensive one. Rank candidates by kill time, survival, capacitor endurance and price together; do not stop at the first legal fit.

## Optional EVEShip.fit MCP

If the runtime already provides the EVEShip.fit MCP connector
(`https://mcp.eveship.fit/mcp`), use it as an optional second opinion and for
systematic variant testing. Its `find_variations` tool swaps meta and faction
variants into a complete fit and recalculates the result; `compare_fits` shows
every difference between two candidates; `calculate_fit` accepts a damage
profile, security class and beacon. The public server needs an OAuth login with
an EVE character, so it may be absent or unauthenticated. Never block a fit on
it: draft and validate locally first, then use the connector to compare
alternatives. See [references/eveshipfit-mcp.md](references/eveshipfit-mcp.md).

## Workflow

0. Check the trust gate: `python3 scripts/trust.py status`. If no build is approved or an update is pending, run `prepare`, review the source and report, and `approve` before any validation. Never skip this because a version looks familiar.
1. Turn the request into a fit brief: hull, activity, environment, solo/fleet role, budget, and any weapon or tank preference. Fill gaps from the user's wording; ask only what changes the design.
2. Search the public libraries for that hull and role. Prefer a vetted, ready-to-use community fit; record the ship, modules, rigs, drones and ammo of one or two candidates. If sources disagree, prefer the fit whose purpose, environment and date match the request. When the request is general-purpose, collect several baselines and keep the modules and roles that repeat across them.
3. If the libraries have nothing usable, or the user referenced a video, search EVE YouTube for the hull and activity. Run `youtube info` and `youtube fits` to pull description and comment fits. When the text has no usable fit, run `youtube frames`, read the fitting window from the contact sheet, and transcribe the modules, rigs, drones and charges. If no ready-to-use fit turns up anywhere, assemble one from the SDE and the rules below.
4. Draft the fit as EFT text. Keep slot order: low, mid, high, rigs, subsystems, drones, cargo, implants. Charges follow their module after a comma; drones use `xN`. Load charges into ancillary repairers and boosters on the module line (`Small Ancillary Armor Repairer, Nanite Repair Paste`) and keep spare paste or cap boosters in cargo; cargo alone leaves the module unloaded. See [references/eft-format.md](references/eft-format.md).
5. Price the hull, modules, rigs, drones and charges, then decide on implants and boosters using the 20% and 10% limits below. Run `checknames`, then `validate`. Resolve every unknown name and every violation. When comparing weapon, tank, propulsion or rig swaps, validate each complete candidate; never reject a higher-DPS variant without an all-V result. Recover CPU, powergrid or calibration with fitting rigs and implants before accepting a module downgrade; see [references/fitting-constraints.md](references/fitting-constraints.md) and [references/budget-implants-boosters.md](references/budget-implants-boosters.md).
6. Iterate on the design, not just the numbers. Run a small matrix over hardener type, repair type, buffer, rigs, cheap consumables and orbit radius; include the highest-DPS legal variant and the safest tank or capacitor variant, even when you expect one to lose. Score each row by kill time, time-to-die, capacitor endurance, price and fitting headroom, then keep the best. Check that tank, damage application, range, speed and capacitor still serve the stated purpose after each downgrade or swap. If the EVEShip.fit MCP connector is available, use `find_variations` and `compare_fits` to test the shortlisted swaps in the complete fit; otherwise use `attrs` and repeated local `validate` runs.
7. If the user asks how the fit fares against another ship, simulate the matchup on realistic terms: both ships moving, the defender at its actual resists, and projected effects from both sides applied. Cover more than one range band and transversal if the answer changes with them; do not report paper DPS against a stationary target as the result.
8. Deliver the final EFT block, a one-line validation result (CPU/PG/calibration, EHP, DPS, cap stability), the source fit with its URL and video timestamp when applicable, and the main adaptations you made. Name any implants and boosters, their effect, and their price share of the base fit. For a matchup, add the assumptions and the ranges where the outcome changes.

## Answer shape

Lead with the EFT block. Follow it with the validation line and two or three sentences on why the fit works for the request, including any assumption about skills (`all V`), implants, or fleet support. When the user gave a budget or alpha constraint, state the downgrades needed for it. Say whether the fit validates without its implants and boosters, and give the current market price used for each one.

If the fit is a doctrine or fleet role, mention the expected fleet context and any links to the source doctrine. If a video fit was transcribed from the screen, say so and name the video and timestamp so the user can compare.

For a matchup, give the result per range band rather than one number: applied damage after tracking and resists, effective tank, speed and tackle control, capacitor pressure, and which projected effects decide the fight. Name the assumptions (transversal, starting range, whether both sides are tackled, implants and links). If the outcome depends on piloting or on a module the user does not have, say so.

When the opponent fit came from the user, say that the calculation uses that exact fit. When it came from killmail, give the sample count and date range and never call one loss the most common fit. If a higher-DPS variant was rejected, name the exact validation constraint and report the chosen fit's CPU, powergrid and calibration headroom.
