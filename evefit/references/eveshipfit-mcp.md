# Optional EVEShip.fit MCP connector

EVEShip.fit runs a public MCP server at `https://mcp.eveship.fit/mcp`. It uses
the same fitting engine as the local `dogma-engine`, exposes the current SDE,
and adds tools that are useful when choosing between variants:

| Tool | Use |
|---|---|
| `calculate_fit` | DPS, volley, EHP, resists, capacitor, speed, targeting, fitting use and rule violations |
| `compare_fits` | every stat that differs between two fits, plus items and rules unique to each |
| `find_variations` | swaps each meta, faction, deadspace or officer variant of an item into a complete fit and recalculates it |
| `get_attributes` | raw attributes of the ship, item or charge, with what changed them |
| `find_type` | exact item names by category |
| `convert_fit` | esf/1, EFT and ESI fitting JSON |

Fits can be sent as EFT, esf/1, DNA, ESI fitting JSON or ESI killmail JSON.
Skills default to all level V. `calculate_fit`, `compare_fits`,
`find_variations` and `get_attributes` also accept a damage profile, security
class, beacon and individual skill levels.

## Access

The public server requires an OAuth login with an EVE Online character. The
login asks for no scopes and reads nothing from the account, but it still needs
a browser and a user present. A skill run cannot authenticate headlessly, and
the repository must not store an EVE password or reuse someone else's token.

Add the server in a client that supports streamable HTTP MCP:

```bash
codex mcp add eveship-fit --url https://mcp.eveship.fit/mcp
codex mcp login eveship-fit
```

The equivalent Claude Code command is:

```bash
claude mcp add --transport http eveship-fit https://mcp.eveship.fit/mcp
```

The server allows 60 requests and 10 seconds of CPU per character per minute.
Long calls are logged with the fit, so send only fits the user asked about.

## When to use it

Use the connector when it is already authenticated in the runtime and the fit
choice benefits from systematic comparison:

1. Draft the fit and validate it locally first. The local `checknames` and
   `validate` path remains the baseline and always works offline.
2. Call `find_variations` for the module that is tight on CPU, powergrid or
   calibration. Compare the actual fit stats and violations, not the module's
   headline bonus.
3. Call `compare_fits` for two candidate fits or for the source fit and the
   adapted fit. Use the differences to decide what changed, including rules
   one side breaks.
4. Call `calculate_fit` with the target's damage profile when a tank number
   needs to be honest about the incoming damage split. Use `security` and
   `beacon` for wormhole or system effects.
5. Convert the final fit back to EFT with `convert_fit` if the working format
   was esf/1, then run local `checknames` and `validate` on the delivered block.

Do not make delivery depend on the connector. If it is absent,
unauthenticated or rate-limited, continue with the local SDE and
`dogma-engine`; note any comparison that could not be run.

## Limits

- The connector is a remote service. Do not paste private notes, API keys or
  unrelated personal data into a fit.
- It calculates a fit, not a fight. Projected effects and piloting still need
  the assumptions in [matchups.md](matchups.md).
- `find_variations` can return many variants. Filter by fitting use and role
  before checking attributes; do not turn the answer into a catalogue.
- A self-hosted instance can run with `NO_LOGIN=true`, but that is a separate
  setup and is not assumed by this skill.
