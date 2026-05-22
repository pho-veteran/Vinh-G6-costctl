# Cost Command Design

## Goal
Implement `./costctl.py cost --tag <key=value> --days N` in `commands/cost_cmd.py` so it queries AWS Cost Explorer, aggregates unblended cost by AWS service over the requested date window, and prints either a sorted cost report or a friendly no-data message.

## Scope
This design covers only the `cost` command.

In scope:
- parsing `args.tag` with `parse_kv`
- computing the requested date range from `args.days`
- calling AWS Cost Explorer with a tag filter and service grouping
- aggregating daily service costs into one per-service total
- formatting terminal output
- handling the normal no-data case with a friendly message
- verifying the command against the real AWS account and rerunning the existing test suite for regression safety

Out of scope:
- changes to `costctl.py`
- adding a new test file
- refactoring other commands
- changing error handling across the CLI
- any write operation against AWS

## Files
- Modify: `commands/cost_cmd.py`
- Read-only verification artifacts after implementation:
  - `output/cost_current_behavior_2026-05-22.txt`
  - replacement live output file captured after the command works

## Recommended Approach
Keep the implementation minimal and local to `run(args)` in `commands/cost_cmd.py`.

Reasoning:
- the repo already uses straightforward command-local implementations
- there is no existing test file driving a helper-based design here
- this command only needs one AWS API call and one formatted report
- smaller scope reduces risk while preserving readability

## Data Flow
1. Parse `args.tag` using `parse_kv(args.tag)` into `tag_key` and `tag_value`.
2. Compute:
   - `end = date.today()`
   - `start = end - timedelta(days=args.days)`
3. Call:

```python
ce = boto3.client("ce")
resp = ce.get_cost_and_usage(
    TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
    Granularity="DAILY",
    Metrics=["UnblendedCost"],
    Filter={"Tags": {"Key": tag_key, "Values": [tag_value]}},
    GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
)
```

4. Iterate `resp["ResultsByTime"]`.
5. For each group in each day:
   - read the service name from `group["Keys"][0]`
   - read the amount string from `group["Metrics"]["UnblendedCost"]["Amount"]`
   - cast to `float`
   - add into a per-service accumulator
6. Sort services by descending total cost.
7. Print the report.
8. If no grouped costs are returned, print the friendly no-data message instead.

## Output Rules

### Success path
Print this shape:

```text
Cost for Project=hexacode over last 7 days (YYYY-MM-DD → YYYY-MM-DD):
------------------------------------------------------------
  Amazon Elastic Compute Cloud - Compute        $    8.42
  Amazon Relational Database Service            $    5.18
------------------------------------------------------------
  TOTAL                                         $   13.60
```

Formatting rules:
- header uses the original tag string and requested day count
- header shows the exact computed start and end dates in ISO format
- services are sorted descending by total cost
- amounts print with two decimals
- total is the sum of all per-service totals

### No-data path
Print exactly this message shape:

```text
No cost data found for Project=hexacode over last 7 days.
```

This is the chosen behavior when Cost Explorer returns no matching groups for the tag and time range.

## Error Handling
Keep this change narrow.

Planned behavior:
- explicitly handle only the normal no-data case
- do not add a broad `try/except` wrapper unless a real Cost Explorer failure is observed during verification and a targeted fix is needed

Implication:
- permission errors, disabled Cost Explorer, or inactive cost allocation tags may still surface as AWS client errors during early verification
- that is acceptable for this implementation scope unless a concrete live failure requires a follow-up design change

## Constraints and Assumptions
- `args.days` is already parsed as an `int` by `argparse`
- the existing default is `7`
- Cost Explorer data can lag by 8–24 hours
- tag-based CE filtering only works if the tag is activated as a cost allocation tag in Billing
- the repo currently has no automated tests for `cost`
- this feature must remain read-only against AWS

## Verification Plan
1. Run a real command against the configured account:

```bash
./costctl.py cost --tag Project=hexacode --days 7
```

2. Accept either of these as correct outcomes:
   - a real grouped cost report
   - the chosen friendly no-data message

3. If the command succeeds, capture truthful stdout into a real output artifact under `output/`.

4. Run the existing regression suite:

```bash
C:/Python314/python.exe -m pytest -v tests/
```

Expected: the current 25 tests still pass.

## Minimality Rules
- no new module-level helpers unless the implementation becomes unreadable without one
- no new files required for the feature itself
- no changes to other command modules
- no speculative retry logic
- no extra flags or output modes

## Commit Prefix Guidance
When implementation starts, use:
- `feat:` for the command implementation
- `docs:` only if output or README documentation changes
- `todo:` only if `TODO.md` changes
