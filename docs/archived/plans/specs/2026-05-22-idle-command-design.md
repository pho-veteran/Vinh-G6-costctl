# Idle Command Design

## Goal
Implement `./costctl.py idle --threshold <cpu_percent> --hours N` in `commands/idle_cmd.py` so it scans running EC2 instances, shows skipped `keep=true` instances, classifies the rest by average CPU utilization over the requested lookback window, and prints a truthful idle summary.

## Scope
This design covers only the `idle` command.

In scope:
- implementing `_avg_cpu(cw, instance_id, hours)`
- implementing `run(args)`
- scanning running EC2 instances only
- skipping instances tagged `keep=true` while still printing them as skipped
- classifying instances as `IDLE`, active, or `NO DATA`
- formatting terminal output
- verifying the command against the real AWS account and capturing truthful output
- rerunning the existing test suite for regression safety

Out of scope:
- changes to `costctl.py`
- adding a new test file
- refactoring other commands
- changing idle selection rules beyond the existing docstring requirements
- any write operation against AWS

## Files
- Modify: `commands/idle_cmd.py`
- Read-only verification artifacts after implementation:
  - `output/idle_current_behavior_2026-05-22.txt`
  - replacement live output file captured after the command works

## Recommended Approach
Keep the implementation minimal and local to `commands/idle_cmd.py`.

Reasoning:
- the repo already uses straightforward command-local implementations
- the command needs one helper for CloudWatch averaging and one entry point for EC2 scanning
- printing skipped `keep=true` instances is easier to understand than silently omitting them
- smaller scope reduces risk while preserving readability

## Data Flow
1. In `run(args)`, create:
   - `ec2 = boto3.client("ec2")`
   - `cw = boto3.client("cloudwatch")`
2. Print a header describing the threshold and hour window.
3. Query EC2 for running instances only.
4. Iterate the returned instances.
5. For each instance:
   - read `InstanceId`
   - read `InstanceType`
   - convert tags with `tags_to_dict`
6. If the instance tag map contains `keep=true`:
   - print a row marking the instance as skipped
   - do not call CloudWatch for that instance
7. Otherwise call `_avg_cpu(cw, instance_id, args.hours)`.
8. `_avg_cpu()` computes:
   - `end = datetime.now(timezone.utc)`
   - `start = end - timedelta(hours=hours)`
   - `cw.get_metric_statistics(...)` with `MetricName="CPUUtilization"`, one `InstanceId` dimension, `Period=3600`, and `Statistics=["Average"]`
9. `_avg_cpu()` behavior:
   - if no datapoints are returned, return `None`
   - otherwise average the datapoint `Average` values with `statistics.mean`
10. Back in `run(args)`:
    - if `_avg_cpu()` returns `None`, print `NO DATA`
    - if the average is below `args.threshold`, print `<- IDLE` and add the instance ID to the final idle list
    - otherwise print the numeric CPU average with no idle marker
11. After all rows, print a separator plus the final idle summary and terminate tip.

## Output Rules

### Header
Print this shape:

```text
Scanning running EC2 (excluding keep=true) — threshold 5.0% over 24h:
------------------------------------------------------------------------------
```

The header text may still say `excluding keep=true` even though skipped rows are shown; the meaning is that those instances are excluded from evaluation, not hidden from output.

### Per-instance rows
Print one row per running instance using these shapes:

```text
  i-0abc123def456789a   t3.micro     cpu_24h= 1.20%  <- IDLE
  i-0bbb456ef789012345  t3.small     cpu_24h=42.50%
  i-0ccc789f0123456789  t3.nano      cpu_24h=NO DATA
  i-0ddd111aaa222bbb3   t3.medium    SKIP keep=true
```

Formatting rules:
- include instance ID and instance type on every row
- for evaluated instances, show `cpu_<hours>h=`
- numeric averages print with two decimals and a trailing percent sign
- `NO DATA` means CloudWatch returned zero datapoints
- `SKIP keep=true` means the tag excluded the instance from evaluation
- append `<- IDLE` only when the numeric average is strictly below the threshold

### Summary
Print this shape after the rows:

```text
------------------------------------------------------------------------------

Idle: 1 instance(s): ['i-0abc123def456789a']
Tip: combo with terminate →  ./costctl.py terminate ec2 --id <id>
```

If no instances are idle, the summary should truthfully print `Idle: 0 instance(s): []`.

## Error Handling
Keep this change narrow.

Planned behavior:
- explicitly handle only the normal no-datapoint case from CloudWatch by returning `None`
- do not add a broad `try/except` wrapper unless a real AWS failure is observed during verification and a targeted fix is needed

Implication:
- EC2 permission errors or CloudWatch permission errors may still surface as AWS client errors during verification
- that is acceptable for this implementation scope unless a concrete live failure requires a follow-up design change

## Constraints and Assumptions
- `args.threshold` is already parsed as a `float` by `argparse`
- `args.hours` is already parsed as an `int` by `argparse`
- the command remains read-only against AWS
- new or very recent instances may have zero CloudWatch datapoints
- `keep=true` matching is exact and case-sensitive for this scope
- the repo currently has no automated tests for `idle`

## Verification Plan
1. Run a real command against the configured account:

```bash
./costctl.py idle --threshold 5 --hours 24
```

2. Accept any truthful outcome, including:
   - one or more rows marked `IDLE`
   - zero idle instances
   - rows containing `NO DATA`
   - rows containing `SKIP keep=true`

3. If the command succeeds, capture truthful stdout into a real output artifact under `output/`.

4. Run the existing regression suite:

```bash
C:/Python314/python.exe -m pytest -v tests/
```

Expected: the current test suite still passes.

## Minimality Rules
- no new files required for the feature itself
- no changes to other command modules
- no speculative retry logic
- no extra flags or output modes
- keep helper scope limited to `_avg_cpu()` plus `run(args)`

## Commit Prefix Guidance
When implementation starts, use:
- `feat:` for the command implementation
- `docs:` only if output or README documentation changes
- `todo:` only if `TODO.md` changes
