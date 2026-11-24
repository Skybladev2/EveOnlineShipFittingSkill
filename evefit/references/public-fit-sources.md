# Public fit sources

Use these sites as baselines. Browse is public on all of them; creating or publishing fits usually needs an EVE SSO account. Search with the site's own filter first, then a web search such as `site:eveworkbench.com Rifter abyss` when the site is JavaScript-only.

| Source | URL | Best for | Notes |
|---|---|---|---|
| EVE Workbench | https://eveworkbench.com/fits | General PvP/PvE library, searchable by hull and modules | Also has doctrines at /doctrines; the largest general baseline |
| KillSync | https://killsync.link/fits-listings | Community fits tagged by activity | Fit workbench at /fits; good for recent meta |
| EVE-Kill | https://eve-kill.com/fits | Popular fits derived from killmails plus shared fits | Killmail popularity is not a purpose filter; check the fit's tags |
| Capsuleers | https://capsuleers.app/tools/fit/public | Public fits from a Pyfa-parity tool | Small library, useful cross-check |
| DaOpa's Fittings Database | https://gamingwithdaopa.ellatha.com/eveonline/fittings-database/ | PvE, missions, Abyss, mining; ~2,200 fits | EFT export, DPS/EHP/cost/skills listed |
| Minmatar Fleet | https://my.minmatar.org/ships/fittings/ | Faction warfare, solo plex, nanogang, fleet | 248 doctrine fits; strongest for Minmatar FW |
| Down the Chain | https://downthechain.net/fits/ | Lowsec and wormhole PvE | Each fit states cost, date, skills and sites cleared |
| Abyss Tracker | https://abysstracker.com/fits | Abyssal Deadspace | Fits paired with run results; check runs, success rate and ISK/hour before copying |
| EVE-Mining | https://eve-mining.com/fits | Mining, ice, gas, moon mining, hauling, scanning | Russian UI with partial English; role-specific |
| EVE Frigates — Faction Warfare Yearbook | https://www.patreon.com/EVEFrigates | Detailed faction-warfare fits, rationale, matchups and tactics for frigates and destroyers | 2026 edition: https://www.patreon.com/EVEFrigates/posts/eve-online-2026-171374966 — strongest textual source for solo/small-gang FW; check for a newer edition |
| iBeast (boosty.to) | https://boosty.to/ibeast | Recent fits, frequently screenshot-only | Posts are mostly fitting-window images with no free text; transcribe with vision and validate every item |
| zkillboard | https://zkillboard.com | PvP fittings recorded on killmails | Bot-protected; use search and character pages, never crawl the kill feed |

## How to use a baseline

1. Prefer a vetted, ready-to-use community fit: a published doctrine or library fit with a stated purpose, a recent date and signs of repeated use. Match hull and purpose first, then environment. A nullsec doctrine fit flown in a wormhole needs different resists, prop and cap. For PvP, cross-check the library fit against current killmail losses of the same hull in the same space.
2. Copy the module list, rigs, drones and ammo exactly into a local `.eft` file.
3. Run `evefit.py validate` on it before changing anything. Old public fits often predate balance patches, so expect CPU/PG or calibration drift.
4. Adapt toward the user's budget and skill assumptions; record what changed. If no ready-to-use fit exists, assemble one from the SDE and the fitting rules. Either path ends with `checknames` and `validate`; community reputation never replaces a formal check.

Fit editors such as https://eveship.fit, https://www.eve-webtools.com/Fitlab/ and https://evefit.online can render a shared fit but are not browsable libraries, so use them only to inspect a specific link.

Since most requests are for general-purpose fits rather than one known
opponent, treat the libraries as a set of baselines: collect two or three
current fits for the hull and role, keep the modules and choices that repeat
across them, and treat the outliers as options. Do not average modules into a
fit that no pilot flies; pick one baseline and adapt it.

## Abyss Tracker performance

Abyss Tracker's value is the run history attached to each fit, not just the EFT
text. A fit that completes the requested Abyssal content repeatedly is stronger
evidence than a fit that looks good on paper.

1. Search https://abysstracker.com/fits by hull, role and Abyssal difficulty.
2. Open the fit and read its performance statistics before copying it: number
   of runs, success or survival rate, average run time, ISK/hour, loot value,
   and the tier and weather those runs used.
3. Prefer fits with many recent runs and proven efficiency at the requested
   difficulty, such as the established Povertila fit, over a newly posted fit
   with no results.
4. Compare like with like. A T5 Exotic success rate does not establish a T6
   Dark run, and old results may predate a balance change or a fit revision.
5. Read the actual EFT and run `checknames` and `validate`. If the page shows no
   run statistics, label the fit unproven and use it only as a baseline.

State the performance evidence in the answer: runs, success rate, tier and
weather, and ISK/hour when the site provides them.

## YouTube channels

EVE YouTubers publish fits in video descriptions, pinned comments and comment threads, and frequently show the fitting window on screen. Use them after the sites above, or when the user points at a specific video. Video content is a proposal from a player, not a data source, so every extracted fit still goes through `checknames` and `validate`.

Useful channels for fitting content include Suitonia, Bjorn Bee, Chessur and Delonewolf; search for `<hull> <activity> fit` to find current videos for a specific hull. Rules for extracting a fit from a description, a comment or a frame, including timestamps and the image budget, are in [youtube-fits.md](youtube-fits.md).

## Screenshot-only fits (iBeast and similar)

Some active publishers post fits only as fitting-window screenshots. Treat a
screenshot as a valid baseline, but transcribe it carefully and prove the
result before delivering.

1. Open the post at https://boosty.to/ibeast and note the post URL, publication
   date and the image position within the gallery.
2. Read the fitting window in slot order: hull and fit name first, then low,
   mid, high, rigs, drones, cargo, implants and boosters. Fitting windows show
   slots in that order.
3. Capture each module's exact name, including meta level and faction prefix,
   and any charge loaded on the same row (`Small Ancillary Armor Repairer,
   Nanite Repair Paste`). Record quantities for drones (`xN`) and cargo.
4. Treat a visible orbit or keep-at-range value as pilot intent, not as the
   real orbit; convert it with the propulsion offset in
   [matchup-scoring.md](matchup-scoring.md).
5. Run `checknames` on the transcript. If a name no longer exists after a
   balance patch, find the current equivalent with `search` and record the
   substitution.
6. Run `validate` at all V. A screenshot can show a fit that no longer fits
   after a patch, so fix CPU, powergrid or calibration before delivery.
7. Cite the post URL and image position (and date) in the answer.

Image budget: inspect one image or one contact sheet at a time, and keep the
whole conversation under the provider limit of 16 images. If a gallery is
large, transcribe the single fitting window that matters and note the others
as unread rather than attaching all of them.

## zkillboard for PvP fits

zkillboard is the best record of what PvP pilots actually fly, but the site has
bot protection and a deep feed. Search narrowly instead of walking recent
kills.

1. Resolve the hull's type ID from the SDE (`evefit.py ship "<Hull>"` or the
   types data), then open the ship page at
   `https://zkillboard.com/ship/<typeID>/`, or use the site search at
   `https://zkillboard.com/search/`. For a bounded read-only sample, the recent
   loss endpoint `https://zkillboard.com/api/shipID/<typeID>/losses/` returns
   killmail IDs and hashes; fetch individual killmails from ESI for item lists.
   Keep requests sparse.
2. Narrow with the site's own filters: date range (last 90 days, or since the
   last balance patch), region or system matching where the user flies, and
   solo/fleet and ship-class filters where available.
3. Find high-efficiency pilots. Look at kill/loss ratio and ISK efficiency on
   recent activity in that hull, and for names that keep appearing. A pilot
   with many losses but a strong efficiency is flying aggressively and still
   winning most exchanges; a pilot with one lucky kill is not evidence.
4. Open those pilots' losses of the requested ship and read the fitting. Collect
   several losses, not one. Keep zkillboard's `solo` label separate from a true
   one-attacker fight: fetch the ESI killmail and check the attacker count.
   Count only fitted modules (low, mid, high and rig flags) and charges loaded
   in weapon slots; cargo can carry spare ammo or modules that were not part of
   the fit. Modules repeated across independent pilots are the real baseline;
   a single unusual fit may be bait, an experiment or a loss caused by a blob.
5. Exclude fittings from fights that do not match the user's scenario: a
   solo-fit ship killed by a 20-ship fleet says little about a solo matchup.
6. Verify every extracted module with `checknames` and run `validate` before
   delivering. Killmail data is a historical record, not a current guarantee.
7. If you describe a layout as common, typical, representative or dominant,
   report the date window, the number of qualifying losses, and the number
   using that exact fitted signature or the key modules. If no signature
   repeats, say the sample is heterogeneous instead of choosing one loss and
   presenting it as the meta.

## Reporting killboard evidence

A killmail is a loss record, not a win-rate sample. Make the evidence match the
claim:

- Say whether the target fit was supplied by the user or inferred from losses.
  A user-supplied target is authoritative and should replace any inferred one.
- Give the date window, hull, filter and sample size (`16 one-attacker solo
  losses from 22–24 November`).
- Count fitted modules and loaded weapon charges, not cargo. A spare damage
  type in cargo does not make a fit that ammo type.
- Report exact fit counts or key-module counts. "Seven launchers appeared in
  3 of 16; six appeared in 10" is evidence. "This is the current solo fit"
  from one killmail is not.
- State what the sample cannot prove: lossmails do not show win rate, pilot
  intent or whether the layout is used most often.

If a page is blocked or the search UI will not load, use a normal web search
such as `site:zkillboard.com <hull> <module>` to find the same kill page, and
fall back to EVE-Kill or other killboards for the same hull. Keep requests
sparse: no crawling, no rapid paging, and no requests for dozens of kills at
once.
