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
| Abyss Tracker | https://abysstracker.com/fits | Abyssal Deadspace | Fits paired with run results and loot |
| EVE-Mining | https://eve-mining.com/fits | Mining, ice, gas, moon mining, hauling, scanning | Russian UI with partial English; role-specific |
| zkillboard | https://zkillboard.com | PvP fittings recorded on killmails | Bot-protected; use search and character pages, never crawl the kill feed |

## How to use a baseline

1. Prefer a vetted, ready-to-use community fit: a published doctrine or library fit with a stated purpose, a recent date and signs of repeated use. Match hull and purpose first, then environment. A nullsec doctrine fit flown in a wormhole needs different resists, prop and cap. For PvP, cross-check the library fit against current killmail losses of the same hull in the same space.
2. Copy the module list, rigs, drones and ammo exactly into a local `.eft` file.
3. Run `evefit.py validate` on it before changing anything. Old public fits often predate balance patches, so expect CPU/PG or calibration drift.
4. Adapt toward the user's budget and skill assumptions; record what changed. If no ready-to-use fit exists, assemble one from the SDE and the fitting rules. Either path ends with `checknames` and `validate`; community reputation never replaces a formal check.

Fit editors such as https://eveship.fit, https://www.eve-webtools.com/Fitlab/ and https://evefit.online can render a shared fit but are not browsable libraries, so use them only to inspect a specific link.

## YouTube channels

EVE YouTubers publish fits in video descriptions, pinned comments and comment threads, and frequently show the fitting window on screen. Use them after the sites above, or when the user points at a specific video. Video content is a proposal from a player, not a data source, so every extracted fit still goes through `checknames` and `validate`.

Useful channels for fitting content include Suitonia, Bjorn Bee, Chessur and Delonewolf; search for `<hull> <activity> fit` to find current videos for a specific hull. Rules for extracting a fit from a description, a comment or a frame, including timestamps and the image budget, are in [youtube-fits.md](youtube-fits.md).

## zkillboard for PvP fits

zkillboard is the best record of what PvP pilots actually fly, but the site has
bot protection and a deep feed. Search narrowly instead of walking recent
kills.

1. Resolve the hull's type ID from the SDE (`evefit.py ship "<Hull>"` or the
   types data), then open the ship page at
   `https://zkillboard.com/ship/<typeID>/`, or use the site search at
   `https://zkillboard.com/search/`.
2. Narrow with the site's own filters: date range (last 90 days, or since the
   last balance patch), region or system matching where the user flies, and
   solo/fleet and ship-class filters where available.
3. Find high-efficiency pilots. Look at kill/loss ratio and ISK efficiency on
   recent activity in that hull, and for names that keep appearing. A pilot
   with many losses but a strong efficiency is flying aggressively and still
   winning most exchanges; a pilot with one lucky kill is not evidence.
4. Open those pilots' losses of the requested ship and read the fitting. Collect
   three to five losses, not one. Modules repeated across independent pilots
   are the real baseline; a single unusual fit may be bait, an experiment or a
   loss caused by a blob.
5. Exclude fittings from fights that do not match the user's scenario: a
   solo-fit ship killed by a 20-ship fleet says little about a solo matchup.
6. Verify every extracted module with `checknames` and run `validate` before
   delivering. Killmail data is a historical record, not a current guarantee.

If a page is blocked or the search UI will not load, use a normal web search
such as `site:zkillboard.com <hull> <module>` to find the same kill page, and
fall back to EVE-Kill or other killboards for the same hull. Keep requests
sparse: no crawling, no rapid paging, and no requests for dozens of kills at
once.
