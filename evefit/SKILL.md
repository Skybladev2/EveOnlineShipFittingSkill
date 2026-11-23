---
name: evefit
description: Build, adapt, and verify EVE Online ship fits from public fit baselines (websites, zkillboard, and YouTube descriptions, comments or on-screen fitting windows), the current official SDE, and dogma-engine, delivering a flyable EFT fit. Use when asked to create a ship fitting, improve or check a fit, compare two ships in a matchup, or explain what a hull can field.
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
python3 scripts/evefit.py update                # download + index latest SDE (cached, ~15 s)
python3 scripts/evefit.py env update            # refresh dogma-engine's SDE package
python3 scripts/evefit.py ship "Rifter"         # slots, CPU/PG, calibration, drones, rig size
python3 scripts/evefit.py search "500MN MWD"    # exact SDE type names
python3 scripts/evefit.py attrs "10MN AB II"    # dogma attributes and skill requirements
python3 scripts/evefit.py checknames fit.eft    # verify every item name against the SDE
python3 scripts/evefit.py validate fit.eft      # all-V calculation; exit 2 on violations
python3 scripts/evefit.py validate - < fit.eft  # read EFT from stdin
python3 scripts/evefit.py validate fit.eft --eft-only   # clean EFT block only
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
- **Community fit first.** Prefer a fit the community has already vetted: a published doctrine or library fit with a stated purpose, a recent date, and repeated use. Check [references/public-fit-sources.md](references/public-fit-sources.md), then EVE YouTube; for PvP, zkillboard losses are an additional baseline. Copy a ready-to-use fit when it matches the hull, role and environment. Only when no usable fit exists, assemble one from first principles. A ready-to-use fit is a starting point, never a substitute for validation: every fit, adapted or home-made, runs through `checknames` and `validate` against the current SDE and dogma-engine before delivery.
- **YouTube order: text before images.** Read the video description and comments first; they often contain an EFT block or a corrected variant. Extract frames only when no usable text fit exists, or when the description points at a timestamp where the fit is shown. Follow [references/youtube-fits.md](references/youtube-fits.md).
- **Cite video evidence.** When a fit comes from YouTube, give the video URL and the timestamp of the description section, comment or frame. An on-screen fit must survive `checknames` and `validate` before it is delivered.
- **Frame budget.** Inspect one or two contact sheets, then re-extract only the timestamps that show the fitting window. Do not dump or view dozens of frames.
- **Ask when direction is missing.** If the purpose, environment, or role is unclear, or no public fit exists for the request, ask up to three concrete questions before locking the fit: what activity it is for, where it flies (high/low/null/wormhole, PvP or PvE), and solo or fleet with budget/tech level. Do not guess a PvP brawler when the user wanted an Abyssal runner.
- **Current values.** Query hull and module numbers from the cached SDE (`ship`, `attrs`, `search`). Do not trust remembered CPU, powergrid, calibration or slot numbers, and do not treat a video's numbers as current.
- **All-V proof.** Every delivered fit must pass `validate` with all skills at V. State this assumption in the answer; mention if an alpha or lower-skill variant would need changes.
- **Exact names only.** EFT import matches English SDE names. Verify each module with `search` or `checknames` before using it; a guessed meta level or faction prefix will fail.
- **zkillboard is a narrow PvP search, not a feed crawl.** The site has bot protection, so use its search feature to filter by hull, date range, region or system instead of walking the kill feed or paging through recent kills. For a PvP fit, find pilots with high efficiency in that hull (strong kill/loss ratio and ISK efficiency on recent activity), then mine those pilots' losses of the requested ship for fittings. Killmails record what a pilot lost with, so treat repeated modules across several pilots as a baseline, not one loss as a recommendation. Prefer recent kills after the last balance patch, and still run `checknames` and `validate`. See [references/public-fit-sources.md](references/public-fit-sources.md).
- **Rigs and implants change CPU/PG.** When CPU or powergrid is tight, treat rigs and implants as fitting tools before downgrading modules: Processor Overclocking Unit (CPU) or Ancillary Current Router (PG) rigs, and the Zainou 'Gypsy' CPU Management or Inherent Implants 'Squire' Power Grid Management hardwirings. The two hardwirings share implant slot 6, so pick one. Rigs consume calibration. See [references/budget-implants-boosters.md](references/budget-implants-boosters.md) and [references/fitting-constraints.md](references/fitting-constraints.md).
- **Cheap fitting implants.** Price the hull, modules, rigs, drones and charges to get a base fit price; exclude implants and boosters from that total. Add a CPU or powergrid implant when its current market price is under 20% of that base. If several qualify, choose the one that fixes the actual shortfall. State the implant, its effect and its share of the base price.
- **Cheap boosters.** Add a booster that matches the fit's role when one dose costs under 10% of the same base price. Prefer the cheapest grade that gives the needed effect; Synth boosters have no side effects, while stronger grades cost more and can impose drawbacks. State the dose price and what is consumed per fight. Leave boosters out when the user rules them out.
- **Realistic matchups.** When simulating one ship against another, never assume an ideal target or perfect application. Take into account both ships' movement (speed, signature, range control and transversal), the target's actual resist profile and tank, and projected effects from either side (webs, scrams, points, neuts, ECM, damps, tracking disruptors, paints, remote reps and links). State the range, transversal and tackle assumptions behind any DPS, EHP or "who wins" claim. See [references/matchups.md](references/matchups.md).

## Workflow

0. Check the trust gate: `python3 scripts/trust.py status`. If no build is approved or an update is pending, run `prepare`, review the source and report, and `approve` before any validation. Never skip this because a version looks familiar.
1. Turn the request into a fit brief: hull, activity, environment, solo/fleet role, budget, and any weapon or tank preference. Fill gaps from the user's wording; ask only what changes the design.
2. Search the public libraries for that hull and role. Prefer a vetted, ready-to-use community fit; record the ship, modules, rigs, drones and ammo of one or two candidates. If sources disagree, prefer the fit whose purpose, environment and date match the request.
3. If the libraries have nothing usable, or the user referenced a video, search EVE YouTube for the hull and activity. Run `youtube info` and `youtube fits` to pull description and comment fits. When the text has no usable fit, run `youtube frames`, read the fitting window from the contact sheet, and transcribe the modules, rigs, drones and charges. If no ready-to-use fit turns up anywhere, assemble one from the SDE and the rules below.
4. Draft the fit as EFT text. Keep slot order: low, mid, high, rigs, subsystems, drones, cargo, implants. Charges follow their module after a comma; drones use `xN`. See [references/eft-format.md](references/eft-format.md).
5. Price the hull, modules, rigs, drones and charges, then decide on implants and boosters using the 20% and 10% limits below. Run `checknames`, then `validate`. Resolve every unknown name and every violation. Recover CPU, powergrid or calibration with fitting rigs and implants before accepting a module downgrade; see [references/fitting-constraints.md](references/fitting-constraints.md) and [references/budget-implants-boosters.md](references/budget-implants-boosters.md).
6. Iterate on the design, not just the numbers: check that tank, damage application, range, speed and capacitor still serve the stated purpose after each downgrade or swap.
7. If the user asks how the fit fares against another ship, simulate the matchup on realistic terms: both ships moving, the defender at its actual resists, and projected effects from both sides applied. Cover more than one range band and transversal if the answer changes with them; do not report paper DPS against a stationary target as the result.
8. Deliver the final EFT block, a one-line validation result (CPU/PG/calibration, EHP, DPS, cap stability), the source fit with its URL and video timestamp when applicable, and the main adaptations you made. Name any implants and boosters, their effect, and their price share of the base fit. For a matchup, add the assumptions and the ranges where the outcome changes.

## Answer shape

Lead with the EFT block. Follow it with the validation line and two or three sentences on why the fit works for the request, including any assumption about skills (`all V`), implants, or fleet support. When the user gave a budget or alpha constraint, state the downgrades needed for it. Say whether the fit validates without its implants and boosters, and give the current market price used for each one.

If the fit is a doctrine or fleet role, mention the expected fleet context and any links to the source doctrine. If a video fit was transcribed from the screen, say so and name the video and timestamp so the user can compare.

For a matchup, give the result per range band rather than one number: applied damage after tracking and resists, effective tank, speed and tackle control, capacitor pressure, and which projected effects decide the fight. Name the assumptions (transversal, starting range, whether both sides are tackled, implants and links). If the outcome depends on piloting or on a module the user does not have, say so.
