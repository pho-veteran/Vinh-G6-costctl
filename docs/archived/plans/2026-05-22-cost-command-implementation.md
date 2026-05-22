# Cost Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `cost` command in `commands/cost_cmd.py` so it queries AWS Cost Explorer by tag, prints per-service totals plus a total row, and prints a friendly no-data message when nothing matches.

**Architecture:** Keep the change local to `commands/cost_cmd.py`. Implement the full behavior directly in `run(args)` using `parse_kv`, a Cost Explorer client, a per-service accumulator, and formatted stdout. Verification is live-only for the feature itself, plus the existing full pytest suite for regression safety.

**Tech Stack:** Python 3.14, boto3 Cost Explorer client, `collections.defaultdict`, `datetime.date`, `datetime.timedelta`, pytest.

---

## File Structure

- Modify: `commands/cost_cmd.py`
  - Replace the current `NotImplementedError` with the full read-only Cost Explorer implementation.
- Verify after implementation: live CLI run against the configured AWS account.
- Verify after implementation: `C:/Python314/python.exe -m pytest -v tests/`

---

### Task 1: Reproduce the current failing `cost` behavior

**Files:**
- Modify later: `commands/cost_cmd.py:55-69`
- Verify current behavior: live CLI invocation only

- [ ] **Step 1: Run the current `cost` command and verify it fails before implementation**

Run:

```bash
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region us-west-2 cost --tag Project=hexacode --days 7
```

Expected: `NotImplementedError: TODO: implement cost — see module docstring`

- [ ] **Step 2: Confirm the current source still contains the stub**

The relevant block in `commands/cost_cmd.py` should currently be:

```python
def run(args):
    """Entry point.

    Args set by argparse:
        args.tag   — "key=value" string (REQUIRED)
        args.days  — int, default 7
    """
    raise NotImplementedError("TODO: implement cost — see module docstring")
```

---

### Task 2: Implement the `cost` command

**Files:**
- Modify: `commands/cost_cmd.py:55-69`

- [ ] **Step 1: Replace the stubbed `run(args)` with the full implementation**

Update `commands/cost_cmd.py` so the file contents from the imports through `run(args)` become:

```python
import boto3
from collections import defaultdict
from datetime import date, timedelta

from commands._common import parse_kv


def run(args):
    """Entry point.

    Args set by argparse:
        args.tag   — "key=value" string (REQUIRED)
        args.days  — int, default 7
    """
    tag_key, tag_value = parse_kv(args.tag)
    end = date.today()
    start = end - timedelta(days=args.days)

    ce = boto3.client("ce")
    response = ce.get_cost_and_usage(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        Filter={"Tags": {"Key": tag_key, "Values": [tag_value]}},
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    totals = defaultdict(float)
    for day in response.get("ResultsByTime", []):
        for group in day.get("Groups", []):
            service = group.get("Keys", [""])[0]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            totals[service] += amount

    if not totals:
        print(f"No cost data found for {args.tag} over last {args.days} days.")
        return

    rows = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    total = sum(amount for _, amount in rows)

    print(f"Cost for {args.tag} over last {args.days} days ({start.isoformat()} → {end.isoformat()}):")
    print("-" * 60)
    for service, amount in rows:
        print(f"  {service:<45} $ {amount:7.2f}")
    print("-" * 60)
    print(f"  {'TOTAL':<45} $ {total:7.2f}")
```

- [ ] **Step 2: Verify the implementation matches the approved behavior**

Check that the code now does all of these:

```text
- parses args.tag with parse_kv
- computes start and end dates from args.days
- calls ce.get_cost_and_usage with a tag filter and SERVICE grouping
- sums UnblendedCost values per service across all returned days
- prints a friendly no-data message if no groups are returned
- otherwise prints sorted per-service totals and a final TOTAL line
```

---

### Task 3: Verify the live `cost` command behavior

**Files:**
- Modify if needed only after observing a real failure: `commands/cost_cmd.py`
- Capture manually after success: `output/` files as appropriate

- [ ] **Step 1: Run the live `cost` command after implementation**

Run:

```bash
PYTHONIOENCODING=utf-8 "C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region us-west-2 cost --tag Project=hexacode --days 7
```

Expected: one of the following is acceptable:

```text
A) a real grouped cost report with per-service lines and TOTAL
B) No cost data found for Project=hexacode over last 7 days.
```

- [ ] **Step 2: If the command succeeds, capture the truthful current output**

Run:

```bash
DATE=$(date +%F) && PYTHONIOENCODING=utf-8 "C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region us-west-2 cost --tag Project=hexacode --days 7 > "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/output/cost_${DATE}.txt"
```

Expected: `output/cost_<date>.txt` contains the exact stdout from the working command.

- [ ] **Step 3: If AWS returns a real client error, stop and report the exact error instead of broadening scope**

Acceptable stop conditions include:

```text
- Cost Explorer is not enabled
- the Project tag is not activated as a cost allocation tag
- the configured identity lacks ce:GetCostAndUsage permission
```

If one of these occurs, do not add speculative retries or fallback behavior.

---

### Task 4: Run regression verification

**Files:**
- Verify only: `tests/`

- [ ] **Step 1: Run the full test suite**

Run:

```bash
"C:/Python314/python.exe" -m pytest -v tests/
```

Expected: `25 passed`

- [ ] **Step 2: Re-read the changed file and confirm scope stayed minimal**

The final change set for implementation should be limited to:

```text
- commands/cost_cmd.py
- optional new output/cost_<date>.txt capture file if the live run succeeded
```

---

### Task 5: Prepare the checkpoint summary

**Files:**
- Report only

- [ ] **Step 1: Summarize exactly what changed and what was verified**

The checkpoint summary must include:

```text
- what was implemented in commands/cost_cmd.py
- whether the live Cost Explorer run produced a real report, no-data message, or an AWS client error
- whether output/cost_<date>.txt was captured
- whether C:/Python314/python.exe -m pytest -v tests/ still reports 25 passed
- files changed
- a suggested commit message beginning with feat:
```

- [ ] **Step 2: Use this suggested commit message if the implementation succeeds**

```text
feat: implement cost command reporting
```
