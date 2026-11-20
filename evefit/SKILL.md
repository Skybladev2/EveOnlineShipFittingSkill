---
name: evefit
description: Build, adapt, and verify EVE Online ship fits from public fit baselines (websites and YouTube descriptions, comments or on-screen fitting windows), the current official SDE, and dogma-engine, delivering a flyable EFT fit. Use when asked to create a ship fitting, improve or check a fit, or explain what a hull can field.
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
- **Baseline first.** Find a public fit for the same hull and purpose before inventing one. Check the fit libraries in [references/public-fit-sources.md](references/public-fit-sources.md), then EVE YouTube content. Only when no public fit exists, ask for direction and design from first principles.
- **YouTube order: text before images.** Read the video description and comments first; they often contain an EFT block or a corrected variant. Extract frames only when no usable text fit exists, or when the description points at a timestamp where the fit is shown. Follow [references/youtube-fits.md](references/youtube-fits.md).
- **Cite video evidence.** When a fit comes from YouTube, give the video URL and the timestamp of the description section, comment or frame. An on-screen fit must survive `checknames` and `validate` before it is delivered.
- **Frame budget.** Inspect one or two contact sheets, then re-extract only the timestamps that show the fitting window. Do not dump or view dozens of frames.
- **Ask when direction is missing.** If the purpose, environment, or role is unclear, or no public fit exists for the request, ask up to three concrete questions before locking the fit: what activity it is for, where it flies (high/low/null/wormhole, PvP or PvE), and solo or fleet with budget/tech level. Do not guess a PvP brawler when the user wanted an Abyssal runner.
- **Current values.** Query hull and module numbers from the cached SDE (`ship`, `attrs`, `search`). Do not trust remembered CPU, powergrid, calibration or slot numbers, and do not treat a video's numbers as current.
- **All-V proof.** Every delivered fit must pass `validate` with all skills at V. State this assumption in the answer; mention if an alpha or lower-skill variant would need changes.
- **Exact names only.** EFT import matches English SDE names. Verify each module with `search` or `checknames` before using it; a guessed meta level or faction prefix will fail.
- **No zkillboard** as a fit source.

## Workflow

0. Check the trust gate: `python3 scripts/trust.py status`. If no build is approved or an update is pending, run `prepare`, review the source and report, and `approve` before any validation. Never skip this because a version looks familiar.
1. Turn the request into a fit brief: hull, activity, environment, solo/fleet role, budget, and any weapon or tank preference. Fill gaps from the user's wording; ask only what changes the design.
2. Search the public libraries for that hull and role. Record the ship, modules, rigs, drones and ammo of one or two candidates. If sources disagree, prefer the fit whose purpose and environment match the request.
3. If the libraries have nothing usable, or the user referenced a video, search EVE YouTube for the hull and activity. Run `youtube info` and `youtube fits` to pull description and comment fits. When the text has no usable fit, run `youtube frames`, read the fitting window from the contact sheet, and transcribe the modules, rigs, drones and charges.
4. Draft the fit as EFT text. Keep slot order: low, mid, high, rigs, subsystems, drones, cargo, implants. Charges follow their module after a comma; drones use `xN`. See [references/eft-format.md](references/eft-format.md).
5. Run `checknames`, then `validate`. Resolve every unknown name and every violation. Use [references/fitting-constraints.md](references/fitting-constraints.md) for the rule meanings and the usual ways to recover CPU, powergrid or calibration.
6. Iterate on the design, not just the numbers: check that tank, damage application, range, speed and capacitor still serve the stated purpose after each downgrade or swap.
7. Deliver the final EFT block, a one-line validation result (CPU/PG/calibration, EHP, DPS, cap stability), the source fit with its URL and video timestamp when applicable, and the main adaptations you made.

## Answer shape

Lead with the EFT block. Follow it with the validation line and two or three sentences on why the fit works for the request, including any assumption about skills (`all V`), implants, or fleet support. When the user gave a budget or alpha constraint, state the downgrades needed for it.

If the fit is a doctrine or fleet role, mention the expected fleet context and any links to the source doctrine. If a video fit was transcribed from the screen, say so and name the video and timestamp so the user can compare.
