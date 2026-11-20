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

## How to use a baseline

1. Match hull and purpose first, then environment. A nullsec doctrine fit flown in a wormhole needs different resists, prop and cap.
2. Copy the module list, rigs, drones and ammo exactly into a local `.eft` file.
3. Run `evefit.py validate` on it before changing anything. Old public fits often predate balance patches, so expect CPU/PG or calibration drift.
4. Adapt toward the user's budget and skill assumptions; record what changed.

Fit editors such as https://eveship.fit, https://www.eve-webtools.com/Fitlab/ and https://evefit.online can render a shared fit but are not browsable libraries, so use them only to inspect a specific link.

## YouTube channels

EVE YouTubers publish fits in video descriptions, pinned comments and comment threads, and frequently show the fitting window on screen. Use them after the sites above, or when the user points at a specific video. Video content is a proposal from a player, not a data source, so every extracted fit still goes through `checknames` and `validate`.

Useful channels for fitting content include Suitonia, Bjorn Bee, Chessur and Delonewolf; search for `<hull> <activity> fit` to find current videos for a specific hull. Rules for extracting a fit from a description, a comment or a frame, including timestamps and the image budget, are in [youtube-fits.md](youtube-fits.md).

Do not use zkillboard.com as a fit source.
