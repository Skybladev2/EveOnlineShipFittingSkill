# EVE Online Ship Fitting Skill

A Codex/agent skill that builds, adapts and verifies EVE Online ship fits. You
ask for a hull and a purpose ("a solo low-sec PvP Rifter"), and it returns a
ready-to-paste EFT block that has been checked against current game data and
proven flyable in the fitting engine.

The skill lives in [`evefit/`](evefit/SKILL.md); `SKILL.md` is the instruction
file the agent follows, and everything else is its references and tooling.

## How it works

1. **Find a baseline fit.** It looks for a public fit for the same hull and role
   first — fit libraries, PvP losses on zkillboard, and EVE YouTube content,
   reading the video description and comments before extracting frames. Only
   when nothing usable exists does it design from scratch (asking about
   activity, space, and budget first).
2. **Use current numbers.** Module stats, slots, CPU/PG, calibration and skill
   requirements come from the official EVE Static Data Export (SDE), fetched
   table by table from the `sde.evetech.net` HTTP API and cached by release, so
   remembered or outdated numbers are not trusted.
3. **Prove the fit flies.** It normalizes the EFT text, checks every item name
   against the SDE, then runs EVEShip.fit's `dogma-engine` to confirm CPU,
   powergrid, calibration, slots, drones and charges fit with all skills at V.
   It reports EHP, DPS and capacitor stability along with any rule violations.
   Fitting rigs and implants are used to recover CPU or powergrid before a
   module is downgraded; a CPU or powergrid implant is added when it costs
   under 20% of the base fit, and a role-appropriate booster when a dose costs
   under 10%.
4. **Deliver with provenance.** The answer is the EFT block plus a one-line
   validation result, and for video-sourced fits the URL and timestamp of the
   description, comment or frame the fit came from.
5. **Treat matchups as scenarios.** When comparing two ships it accounts for
   speed, range control and transversal, the target's real resists, and
   projected effects such as webs, neuts and ECM, instead of comparing paper
   DPS against an ideal target.

`dogma-engine` ships native code, so the skill has a trust gate: the engine is
downloaded, hashed and reviewed before it is installed, and the approval is
re-checked on every version, wheel or SDE change.

If an EVEShip.fit MCP connector is authenticated in the agent runtime, the skill
can also use its `find_variations`, `compare_fits` and `calculate_fit` tools for
systematic variant checks. This is optional: the connector needs an EVE
character login, and the local SDE and engine remain the fallback.

## Quick start

Requires Python 3 and network access for the first SDE download.

```bash
cd evefit
python3 scripts/trust.py status          # is a reviewed engine version installed?
python3 scripts/trust.py prepare         # fetch the latest engine for review
python3 scripts/evefit.py status         # cached/latest SDE and engine versions
python3 scripts/evefit.py update         # cache changed tables from the latest SDE release
python3 scripts/evefit.py ship "Rifter"  # slots, CPU/PG, calibration
python3 scripts/evefit.py validate fit.eft
```

`validate` exits with code 2 when the fit breaks a fitting rule, which makes it
usable as a check in scripts. YouTube helpers (`evefit.py youtube ...`) install
`yt-dlp` in the skill's private virtualenv on first use.

## Layout

| Path | Purpose |
| --- | --- |
| `evefit/SKILL.md` | Agent instructions: rules, workflow and answer format |
| `evefit/references/` | EFT syntax, fitting constraints, public fit sources, matchup simulation, EVEShip.fit MCP, trust policy, YouTube extraction |
| `evefit/scripts/evefit.py` | SDE cache, searches, EFT validation, YouTube commands |
| `evefit/scripts/evefityt.py` | YouTube metadata, description/comment fits, frame extraction |
| `evefit/scripts/trust.py` | Wheel review, approval and installed-file verification |

Data and the private virtualenv live in the user cache directory
(`~/.cache/evefit` by default, override with `EVEFIT_CACHE`).

## License

The source code and documentation in this repository are released under the
[Unlicense](LICENSE). EVE Online game data and trademarks remain subject to the
notices in [FC.md](FC.md).

## Copyright

EVE Online and the EVE logo are the intellectual property of Fenris Creations
(formerly CCP hf.). See [FC.md](FC.md) for the full notice and the license
terms this project relies on.
