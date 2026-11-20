# Trust gate for dogma-engine

No source code is trusted by default. `eveshipfit-dogma-engine` ships a compiled
native extension, so a wrong build can run with the skill's permissions. The
skill therefore refuses to install or import the engine until the exact wheel
and the source it was built from have been reviewed and recorded.

This applies to the first install and to every update: a new version, a new
wheel hash, or an SDE data package change invalidates the record.

## Policy

1. Download, never install first. `trust.py prepare` fetches the wheel and the
   GitHub tag archive with plain HTTP and unpacks them as data. It does not run
   install hooks, build scripts, or package code.
2. Verify the wheel against PyPI's SHA-256 and the source tag against the GitHub
   commit. `prepare` prints both and refuses on a mismatch.
3. Read the shipped code. Look for process spawning, network clients, dynamic
   execution, credential access, file writes outside the SDE, install hooks,
   obfuscation, and unexpected binaries.
4. Check the diff against the previously approved version, not only the new
   files.
5. Record an approval with review notes. Only then may the engine be installed
   and imported.
6. Re-verify the installed files against the approved wheel before use. An
   installed file that no longer matches its approved hash blocks validation.

## Commands

```bash
python3 scripts/trust.py status
python3 scripts/trust.py prepare                  # latest on PyPI + matching SDE
python3 scripts/trust.py prepare --version 15.2.0
python3 scripts/trust.py approve --version 15.2.0 --notes "what was reviewed"
python3 scripts/trust.py check --require-install
python3 scripts/trust.py adopt --notes "reviewed installed files by hand"
```

The same commands are reachable as `python3 scripts/evefit.py trust ...`.

`prepare` writes `~/.cache/evefit/trust/pending.json`, keeps the downloaded
wheel and extracted source under `~/.cache/evefit/trust/`, and prints:

- PyPI wheel hash and source archive tag/commit;
- a per-file source digest and the changed files versus the approved baseline;
- static-scan findings grouped as high, medium, low or info, with the rule and
  the location.

Approve only after reading the report. High-severity findings block approval
unless `--ack-findings` is passed and the notes explain why they are expected.

## Review checklist

For the Python wheel and the shipped Rust crates (`esf-python`, `esf-data`,
`esf-format`, `esf-dogma-engine`):

- install hooks: `pyproject.toml` build backend, `setup.py`, `build.rs`, custom
  backend modules;
- process execution: `Command::new`, `std::process`, `subprocess`, `os.system`;
- network: `ureq`, `reqwest`, `hyper`, sockets, raw HTTP, DNS;
- dynamic execution: `exec`, `eval`, `__import__`, plugin loading;
- filesystem: writes, deletes, permission changes, paths outside the cache;
- credentials and environment: home directory reads, env scraping, keychains;
- obfuscation: long encoded blobs, invisible Unicode, packed payloads;
- dependency changes: new crates or Python packages with install-time behavior;
- release workflow: trusted publishing, tag/version consistency, unpinned
  actions, artifacts built from the reviewed commit.

Code in `crates/esf-mcp`, `fuzz/` and `tests/` is not shipped in the Python
wheel; findings there are reported as info. Still note any new network or process
code, because it shows intent and may reach other distribution channels.

## Update flow

1. `python3 scripts/evefit.py env update` (or `trust.py prepare`) reports the
   latest versions and prepares a report. It exits without installing.
2. Review the changed files and the scan findings.
3. `python3 scripts/trust.py approve --version V --notes "..."`
4. `python3 scripts/evefit.py env update` installs the verified wheels.
5. `python3 scripts/trust.py check --require-install` confirms every installed
   file matches.

`validate` and YouTube helpers call the same gate. With no approved record, or
with an installed build that differs from it, they stop before importing the
engine and explain how to recover.

## Limits

- A hash proves the wheel is the one PyPI served; it does not prove the build is
  benign. The source review is the actual trust decision.
- PyPI publishes no provenance attestation for 15.2.0 (the provenance endpoint
  returns 404). Provenance rests on the GitHub tag matching the release, the
  release workflow using trusted publishing, and the wheel's SBOM and hashes.
- The wheel contains a native `.so`; static strings and source review reduce but
  cannot eliminate the chance of a backdoor. Treat future versions with extra
  care when the diff touches FFI, networking, or build scripts.
- `adopt` records already installed files after a manual review. It does not
  download or verify PyPI provenance, so use it only for offline recovery and
  re-run `prepare` at the next opportunity.
