# TODO

Track the next feature work based on the current real CLI outputs in `output/`.

## Erroring features to solve next

### feat: implement `cost`
- Evidence: `output/cost_current_behavior_2026-05-22.txt`
- Current behavior: raises `NotImplementedError: TODO: implement cost — see module docstring`
- Next goal:
  - implement `commands/cost_cmd.py`
  - verify with a real read-only run such as `./costctl.py cost --tag Project=hexacode --days 7`
  - replace the error artifact with a real cost report output

### feat: implement `idle`
- Evidence: `output/idle_current_behavior_2026-05-22.txt`
- Current behavior: raises `NotImplementedError: TODO: implement run() — see module docstring`
- Next goal:
  - implement `_avg_cpu()` and `run()` in `commands/idle_cmd.py`
  - verify with a real read-only run such as `./costctl.py idle --threshold 5 --hours 24`
  - capture a truthful idle scan output

### feat: implement `migrate-gp3` dry-run
- Evidence: `output/migrate_gp3_current_behavior_2026-05-22.txt`
- Current behavior: raises `NotImplementedError: TODO: implement migrate-gp3 — see module docstring`
- Next goal:
  - implement `commands/migrate_gp3_cmd.py`
  - verify dry-run only first with `./costctl.py migrate-gp3`
  - do not use `--apply` during read-only verification

## Behavior issue to fix

### feat: make top-level help print on Windows consoles
- Evidence: live verification found `costctl.py --help` fails on this machine unless `PYTHONIOENCODING=utf-8` is set
- Current behavior:
  - Windows console default encoding is `cp1252`
  - top-level help includes `gp2 → gp3 EBS migration`
  - printing `→` causes `UnicodeEncodeError`
- Next goal:
  - make top-level help output ASCII-safe on Windows without requiring an environment workaround
  - re-run `costctl.py --help` normally and confirm it prints successfully

## Not errors, but intentionally skipped
- `tag` was not run live because it modifies AWS resources
- `clean --apply` was not run live because it modifies AWS resources
- `terminate` was only exercised through the abort path because successful execution would modify AWS resources

## Commit prefix practice for the next work
- Use `feat:` for feature implementation work
- Use `docs:` for README or output documentation updates
- Use `todo:` for updates to this file
