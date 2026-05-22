# Idle Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `idle` command in `commands/idle_cmd.py` so it scans running EC2 instances, prints skipped `keep=true` rows, classifies the rest by N-hour average CPU utilization, and reports the final idle instance list.

**Architecture:** Keep the change local to `commands/idle_cmd.py`. Add a small `_avg_cpu()` helper that queries CloudWatch and returns either a numeric average or `None`, then let `run(args)` handle EC2 scanning, row formatting, and final summary output. Verification is a real read-only AWS CLI run plus the existing pytest suite for regression safety.

**Tech Stack:** Python 3.14, boto3 EC2 client, boto3 CloudWatch client, `datetime`, `statistics.mean`, pytest.

---

## File Structure

- Modify: `commands/idle_cmd.py`
  - Replace the current stubs with the full read-only EC2 + CloudWatch implementation.
- Verify after implementation: live CLI run against the configured AWS account.
- Verify after implementation: `C:/Python314/python.exe -m pytest -v tests/`
- Capture after live success: `output/idle_<date>.txt`

---

### Task 1: Reproduce the current failing `idle` behavior

**Files:**
- Modify later: `commands/idle_cmd.py:53-70`
- Verify current behavior: live CLI invocation only

- [ ] **Step 1: Run the current `idle` command and verify it fails before implementation**

Run:

```bash
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region us-west-2 idle --threshold 5 --hours 24
```

Expected: `NotImplementedError: TODO: implement run() — see module docstring`

- [ ] **Step 2: Confirm the current source still contains both stubs**

The relevant block in `commands/idle_cmd.py` should currently be:

```python
def _avg_cpu(cw, instance_id, hours):
    """Return average CPU% over last N hours, or None if no datapoints."""
    raise NotImplementedError("TODO: implement _avg_cpu — use get_metric_statistics")


def run(args):
    """Entry point.

    Args set by argparse:
        args.threshold  — float, default 5.0 (% CPU)
        args.hours      — int, default 24
    """
    raise NotImplementedError("TODO: implement run() — see module docstring")
```

---

### Task 2: Implement the CloudWatch average helper

**Files:**
- Modify: `commands/idle_cmd.py:53-60`

- [ ] **Step 1: Add the shared tag helper import needed by `run(args)`**

Update the imports at the top of `commands/idle_cmd.py` to include:

```python
import boto3
from datetime import datetime, timedelta, timezone
from statistics import mean

from commands._common import tags_to_dict
```

- [ ] **Step 2: Replace the `_avg_cpu()` stub with the real CloudWatch implementation**

Update `commands/idle_cmd.py` so `_avg_cpu()` becomes:

```python
def _avg_cpu(cw, instance_id, hours):
    """Return average CPU% over last N hours, or None if no datapoints."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    response = cw.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=start,
        EndTime=end,
        Period=3600,
        Statistics=["Average"],
    )
    datapoints = response.get("Datapoints", [])
    if not datapoints:
        return None
    return mean(point["Average"] for point in datapoints)
```

- [ ] **Step 3: Re-read the helper and verify its contract matches the approved design**

Check that `_avg_cpu()` now does all of these:

```text
- computes a UTC [start, end] window from args.hours
- queries AWS/EC2 CPUUtilization for exactly one instance ID
- uses 3600-second hourly buckets
- returns None when CloudWatch returns zero datapoints
- returns the mean of datapoint Average values otherwise
```

---

### Task 3: Implement the `idle` command scan and formatting

**Files:**
- Modify: `commands/idle_cmd.py:63-70`

- [ ] **Step 1: Replace the `run(args)` stub with the full implementation**

Update `commands/idle_cmd.py` so `run(args)` becomes:

```python
def run(args):
    """Entry point.

    Args set by argparse:
        args.threshold  — float, default 5.0 (% CPU)
        args.hours      — int, default 24
    """
    ec2 = boto3.client("ec2")
    cw = boto3.client("cloudwatch")
    idle_ids = []

    print(
        f"Scanning running EC2 (excluding keep=true) - threshold {args.threshold:.1f}% over {args.hours}h:"
    )
    print("-" * 78)

    response = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]
            tags = tags_to_dict(instance.get("Tags"))

            if tags.get("keep") == "true":
                print(f"  {instance_id:<21} {instance_type:<12} SKIP keep=true")
                continue

            avg = _avg_cpu(cw, instance_id, args.hours)
            if avg is None:
                print(f"  {instance_id:<21} {instance_type:<12} cpu_{args.hours}h=NO DATA")
                continue

            line = f"  {instance_id:<21} {instance_type:<12} cpu_{args.hours}h={avg:5.2f}%"
            if avg < args.threshold:
                idle_ids.append(instance_id)
                line += "  <- IDLE"
            print(line)

    print("-" * 78)
    print()
    print(f"Idle: {len(idle_ids)} instance(s): {idle_ids}")
    print("Tip: combo with terminate ->  ./costctl.py terminate ec2 --id <id>")
```

- [ ] **Step 2: Verify the implementation matches the approved behavior**

Check that the code now does all of these:

```text
- creates EC2 and CloudWatch clients inside run(args)
- scans only running EC2 instances
- converts AWS tag lists with tags_to_dict(instance.get("Tags"))
- prints keep=true instances as SKIP rows instead of hiding them
- prints NO DATA when _avg_cpu() returns None
- appends <- IDLE only when the numeric average is strictly below args.threshold
- collects idle instance IDs and prints them in the final summary
- uses ASCII output for the tip line so live Windows verification does not depend on a UTF-8 console setting
```

---

### Task 4: Verify the live `idle` command behavior

**Files:**
- Modify if needed only after observing a real failure: `commands/idle_cmd.py`
- Capture manually after success: `output/idle_<date>.txt`

- [ ] **Step 1: Run the live `idle` command after implementation**

Run:

```bash
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region us-west-2 idle --threshold 5 --hours 24
```

Expected: the command completes without `NotImplementedError` and prints a truthful report containing only outcomes actually observed in the account, such as:

```text
- one or more rows with cpu_24h=<number>%
- optional rows with SKIP keep=true
- optional rows with cpu_24h=NO DATA
- optional <- IDLE markers
- a final Idle: <count> instance(s): [...] summary
```

- [ ] **Step 2: If the command succeeds, capture the truthful current output**

Run:

```bash
DATE=$(date +%F) && "C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region us-west-2 idle --threshold 5 --hours 24 > "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/output/idle_${DATE}.txt"
```

Expected: `output/idle_<date>.txt` contains the exact stdout from the working command, even if the summary reports zero idle instances.

- [ ] **Step 3: If AWS returns a real client error, stop and report the exact error instead of broadening scope**

Acceptable stop conditions include:

```text
- the configured identity lacks ec2:DescribeInstances permission
- the configured identity lacks cloudwatch:GetMetricStatistics permission
- the selected region has no accessible instances and the output still truthfully reports none
```

If a real AWS client error occurs, do not add speculative retries, fallback regions, or unrelated error handling.

---

### Task 5: Run regression verification

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
- commands/idle_cmd.py
- optional new output/idle_<date>.txt capture file if the live run succeeded
```

---

### Task 6: Prepare the checkpoint summary

**Files:**
- Report only

- [ ] **Step 1: Summarize exactly what changed and what was verified**

The checkpoint summary must include:

```text
- what was implemented in commands/idle_cmd.py
- whether the live idle run produced active rows, skipped rows, no-data rows, idle rows, or zero idle instances
- whether output/idle_<date>.txt was captured
- whether C:/Python314/python.exe -m pytest -v tests/ still reports 25 passed
- files changed
- a suggested commit message beginning with feat:
```

- [ ] **Step 2: Use this suggested commit message if the implementation succeeds**

```text
feat: implement idle command scan
```
