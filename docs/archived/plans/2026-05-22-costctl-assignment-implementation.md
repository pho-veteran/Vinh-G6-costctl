# Costctl Assignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Dispatch every implementation phase to a fresh Sonnet subagent working inline in the current repository checkout. Strictly do not create, enter, or use git worktrees. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `costctl` starter so automated tests reach `25/25`, add the manual-only `tag` command, and update submission-facing text for `Vinh-G6`.

**Architecture:** Keep the existing argparse entrypoint and command module layout. Implement each command module directly against boto3 clients, using `commands/_common.py` helpers for key/value parsing, tag conversion, tag matching, and confirmation. Preserve destructive-command safety: `terminate` confirms unless forced, and `clean` is dry-run unless `--apply` is passed.

**Tech Stack:** Python 3.11+, boto3, botocore, moto, pytest, GNU Make.

---

## File Structure

- Modify: `commands/list_cmd.py`
  - Implements EC2, RDS, S3, and EBS volume listing helpers.
  - Implements `run(args)` output formatting for the CLI.
- Modify: `commands/terminate_cmd.py`
  - Implements one-resource destructive operations for EC2, RDS, S3, and EBS volumes.
  - Centralizes friendly `ClientError` printing in `run(args)`.
- Modify: `commands/clean_cmd.py`
  - Implements tag-based target discovery for EC2 instances and available EBS volumes.
  - Implements dry-run and apply behavior.
- Modify: `commands/tag_cmd.py`
  - Implements manual-only tag application for EC2, RDS, S3, and EBS volumes.
  - Preserves existing S3 bucket tags by merging before `put_bucket_tagging`.
- Modify: `README.md`
  - Updates visible submission-facing placeholders to `Vinh-G6`.
  - States the final target score as `25/25` after implementation.
  - Keeps sample-output replacement honest: only real AWS output should replace samples.
- Leave unchanged: `tests/*.py`
  - The provided tests are the assignment contract.
- Leave unchanged unless real AWS verification is available: `sample_output/*`
  - Do not fabricate sample output.

## Execution Notes

- Run from repository root: `C:\Users\thanh\Desktop\workspace\xbrain\w6-miniproj\Vinh-G6-costctl`.
- Use `superpowers:subagent-driven-development` for execution. Dispatch each implementation phase to a fresh Sonnet subagent, but keep work inline in this current repository checkout.
- Strict no-worktree rule: do not call `EnterWorktree`, do not run `git worktree`, do not create `.claude/worktrees/`, and do not ask subagents to use worktree isolation. All subagents must edit the current checkout directly.
- Inline subagent execution means the main agent dispatches one Sonnet subagent for the current phase, waits for it to finish, reviews the current-checkout changes, reports the checkpoint, and only then continues when the user approves.
- The provided tests set dummy AWS credentials and region in `tests/conftest.py`, so command modules should use plain `boto3.client("ec2")`, `boto3.client("s3")`, and `boto3.client("rds")`.
- Do not modify `costctl.py`; it already wires all commands and sets `AWS_REGION` / `AWS_DEFAULT_REGION`.
- Do not create commits automatically. At each checkpoint, provide a concise commit-message suggestion without any Claude co-author trailer.

## Checkpoint Rules

Stop and report to the user after each meaningful implementation boundary before continuing. A meaningful boundary includes every command-level side-challenge milestone and any other coherent implementation unit that becomes meaningful during execution. Because execution is inline, do not dispatch the next Sonnet subagent until the current checkpoint has been reported and the user has approved continuing.

At each checkpoint, report:
- what was implemented
- tests or verification commands that passed
- files changed
- a concise suggested commit message, not too short and not too long, with no `Co-Authored-By` trailer

Required checkpoints:
1. After `list` is complete and `pytest tests/test_list.py -v` passes.
2. After `terminate` is complete and `pytest tests/test_terminate.py -v` passes.
3. After `clean` is complete and `pytest tests/test_clean.py -v` passes.
4. After `tag` is implemented and parser/full-suite verification passes or manual AWS verification is explicitly marked pending.
5. After README/submission-facing naming is updated and placeholder checks pass.
6. After final verification and sample-output decision.

Suggested commit messages must look like these examples:
- `Implement list command resource discovery`
- `Implement safe terminate command handling`
- `Implement dry-run clean resource cleanup`
- `Implement tag command for AWS resources`
- `Update Vinh-G6 submission documentation`
- `Complete costctl verification pass`

---

### Task 1: Implement EC2 listing

**Files:**
- Modify: `commands/list_cmd.py:36-52`
- Test: `tests/test_list.py:22-65`

- [ ] **Step 1: Use the existing failing EC2 listing tests as the TDD contract**

The provided tests are already written. The EC2 contract is:

```python
@mock_aws
def test_list_ec2_empty():
    rows = _list_ec2([], [])
    assert rows == []

@mock_aws
def test_list_ec2_no_filter_returns_all():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    _launch(ec2, {"Environment": "dev"})
    _launch(ec2, {"Environment": "prod"})
    rows = _list_ec2([], [])
    assert len(rows) == 2

@mock_aws
def test_list_ec2_filter_by_tag():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    _launch(ec2, {"Environment": "dev"})
    _launch(ec2, {"Environment": "prod"})
    rows = _list_ec2([("Environment", "dev")], [])
    assert len(rows) == 1
    assert rows[0][3]["Environment"] == "dev"

@mock_aws
def test_list_ec2_missing_tag():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    _launch(ec2, {"Application": "HealthBot"})
    _launch(ec2, {"Environment": "dev"})
    rows = _list_ec2([], ["Application"])
    assert len(rows) == 1
    assert "Application" not in rows[0][3]

@mock_aws
def test_list_ec2_combined_tag_and_missing():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    _launch(ec2, {"Environment": "dev", "Owner": "alice"})
    _launch(ec2, {"Environment": "dev"})
    _launch(ec2, {"Environment": "prod", "Owner": "bob"})
    rows = _list_ec2([("Environment", "dev")], ["Owner"])
    assert len(rows) == 1
```

- [ ] **Step 2: Run one EC2 test and verify it fails before implementation**

Run:

```bash
pytest tests/test_list.py::test_list_ec2_empty -v
```

Expected: FAIL with `NotImplementedError: TODO: implement _list_ec2`.

- [ ] **Step 3: Add the `ClientError` import needed by later S3 listing work**

In `commands/list_cmd.py`, replace the import block with:

```python
import boto3
from botocore.exceptions import ClientError

from commands._common import parse_kv, tags_to_dict, tags_match
```

- [ ] **Step 4: Implement `_list_ec2`**

In `commands/list_cmd.py`, replace `_list_ec2` with:

```python
def _list_ec2(want, missing):
    """List EC2 instances matching tag filters.

    Args:
        want: list of (key, value) tag pairs that must all match
        missing: list of tag keys that must NOT be present

    Returns:
        list of (instance_id, instance_type, state, tags_dict) tuples
    """
    ec2 = boto3.client("ec2")
    rows = []
    paginator = ec2.get_paginator("describe_instances")

    for page in paginator.paginate():
        for reservation in page.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                tags = tags_to_dict(instance.get("Tags", []))
                if tags_match(tags, want, missing):
                    rows.append((
                        instance["InstanceId"],
                        instance.get("InstanceType", ""),
                        instance.get("State", {}).get("Name", ""),
                        tags,
                    ))

    return rows
```

- [ ] **Step 5: Run the EC2 listing tests**

Run:

```bash
pytest tests/test_list.py::test_list_ec2_empty tests/test_list.py::test_list_ec2_no_filter_returns_all tests/test_list.py::test_list_ec2_filter_by_tag tests/test_list.py::test_list_ec2_missing_tag tests/test_list.py::test_list_ec2_combined_tag_and_missing -v
```

Expected: all 5 selected tests PASS.

- [ ] **Step 6: Continue list implementation without stopping yet**

Do not stop here unless something unexpected creates a meaningful implementation boundary. EC2 listing is only part of the full `list` command milestone; continue to S3, EBS volume, RDS, and CLI list output before the required `list` checkpoint.

---

### Task 2: Implement S3 and EBS volume listing

**Files:**
- Modify: `commands/list_cmd.py:66-85`
- Test: `tests/test_list.py:68-85`

- [ ] **Step 1: Use the existing S3 and volume tests as the TDD contract**

The provided tests are:

```python
@mock_aws
def test_list_s3_no_tagging_treated_as_empty_tags():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="empty-tag-bucket")
    rows = _list_s3([], ["Application"])
    assert any(r[0] == "empty-tag-bucket" for r in rows)

@mock_aws
def test_list_volume_returns_type_size():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ec2.create_volume(Size=100, VolumeType="gp2", AvailabilityZone="us-east-1a",
                      TagSpecifications=[{"ResourceType": "volume",
                                          "Tags": [{"Key": "purpose", "Value": "practice"}]}])
    rows = _list_volume([("purpose", "practice")], [])
    assert len(rows) == 1
    assert "gp2-100GB" in rows[0][1]
```

- [ ] **Step 2: Run the S3 test and verify it fails before implementation**

Run:

```bash
pytest tests/test_list.py::test_list_s3_no_tagging_treated_as_empty_tags -v
```

Expected: FAIL with `NotImplementedError: TODO: implement _list_s3`.

- [ ] **Step 3: Implement `_list_s3`**

In `commands/list_cmd.py`, replace `_list_s3` with:

```python
def _list_s3(want, missing):
    """List S3 buckets matching tag filters.

    Note: get_bucket_tagging raises ClientError if no tagging config exists
    for that bucket. Treat that as an empty tags dict, not an error.

    Returns:
        list of (bucket_name, "bucket", "active", tags_dict) tuples
    """
    s3 = boto3.client("s3")
    rows = []

    for bucket in s3.list_buckets().get("Buckets", []):
        name = bucket["Name"]
        try:
            tag_set = s3.get_bucket_tagging(Bucket=name).get("TagSet", [])
        except ClientError:
            tag_set = []

        tags = tags_to_dict(tag_set)
        if tags_match(tags, want, missing):
            rows.append((name, "bucket", "active", tags))

    return rows
```

- [ ] **Step 4: Run the S3 test and verify it passes**

Run:

```bash
pytest tests/test_list.py::test_list_s3_no_tagging_treated_as_empty_tags -v
```

Expected: PASS.

- [ ] **Step 5: Run the volume test and verify it fails before implementation**

Run:

```bash
pytest tests/test_list.py::test_list_volume_returns_type_size -v
```

Expected: FAIL with `NotImplementedError: TODO: implement _list_volume`.

- [ ] **Step 6: Implement `_list_volume`**

In `commands/list_cmd.py`, replace `_list_volume` with:

```python
def _list_volume(want, missing):
    """List EBS volumes matching tag filters.

    Returns:
        list of (volume_id, "<type>-<size>GB", state, tags_dict) tuples
        e.g. ("vol-0abc", "gp2-100GB", "in-use", {"purpose": "practice"})
    """
    ec2 = boto3.client("ec2")
    rows = []
    paginator = ec2.get_paginator("describe_volumes")

    for page in paginator.paginate():
        for volume in page.get("Volumes", []):
            tags = tags_to_dict(volume.get("Tags", []))
            if tags_match(tags, want, missing):
                rows.append((
                    volume["VolumeId"],
                    f"{volume.get('VolumeType', '')}-{volume.get('Size', '')}GB",
                    volume.get("State", ""),
                    tags,
                ))

    return rows
```

- [ ] **Step 7: Run the volume test and verify it passes**

Run:

```bash
pytest tests/test_list.py::test_list_volume_returns_type_size -v
```

Expected: PASS.

- [ ] **Step 8: Run the full list test file**

Run:

```bash
pytest tests/test_list.py -v
```

Expected: 7 tests PASS.

- [ ] **Step 9: Continue list implementation without stopping yet**

Do not stop here unless something unexpected creates a meaningful implementation boundary. S3 and EBS volume listing are part of the full `list` command milestone; continue to RDS and CLI list output before the required `list` checkpoint.

---

### Task 3: Implement RDS listing and CLI list output

**Files:**
- Modify: `commands/list_cmd.py:54-110`
- Manual Test: `./costctl.py list ec2` under moto is not directly available through the CLI, so verify with unit tests and a parser smoke test.

- [ ] **Step 1: Implement `_list_rds` from the module docstring**

In `commands/list_cmd.py`, replace `_list_rds` with:

```python
def _list_rds(want, missing):
    """Same shape as _list_ec2 but for RDS DB instances.

    Note: RDS tags require a separate API call per DB:
        rds.list_tags_for_resource(ResourceName=db['DBInstanceArn'])

    Returns:
        list of (db_id, db_class, db_status, tags_dict) tuples
    """
    rds = boto3.client("rds")
    rows = []

    for db in rds.describe_db_instances().get("DBInstances", []):
        tag_list = rds.list_tags_for_resource(
            ResourceName=db["DBInstanceArn"]
        ).get("TagList", [])
        tags = tags_to_dict(tag_list)
        if tags_match(tags, want, missing):
            rows.append((
                db["DBInstanceIdentifier"],
                db.get("DBInstanceClass", ""),
                db.get("DBInstanceStatus", ""),
                tags,
            ))

    return rows
```

- [ ] **Step 2: Add local formatting helpers for `run(args)`**

In `commands/list_cmd.py`, insert these helpers above `run(args)` and below `DISPATCH`:

```python
def _format_tags(tags):
    if not tags:
        return "-"
    return ", ".join(f"{k}={v}" for k, v in sorted(tags.items()))


def _format_filter(args):
    parts = list(args.tag or [])
    parts.extend(f"missing:{key}" for key in (args.missing_tag or []))
    return ", ".join(parts) if parts else "all"
```

- [ ] **Step 3: Implement `run(args)`**

In `commands/list_cmd.py`, replace `run(args)` with:

```python
def run(args):
    """Entry point called by costctl.py.

    Steps you should perform:
      1. Convert args.tag (list of "k=v" strings) → want pairs via parse_kv
      2. Use args.missing_tag (list of keys) as-is
      3. Call DISPATCH[args.type](want, missing) → rows
      4. Print a header line, separator, then one row per resource

    Args set by argparse:
        args.type         — one of "ec2", "rds", "s3", "volume"
        args.tag          — list[str], each "key=value"
        args.missing_tag  — list[str], each "key"
    """
    want = [parse_kv(item) for item in (args.tag or [])]
    missing = args.missing_tag or []
    rows = DISPATCH[args.type](want, missing)

    print(f"{args.type.upper()} {_format_filter(args)} — {len(rows)} found:")
    print("-" * 78)
    for rid, kind, state, tags in rows:
        print(f"  {rid:<24} {kind:<14} {state:<14} {_format_tags(tags)}")
```

- [ ] **Step 4: Run full list tests again**

Run:

```bash
pytest tests/test_list.py -v
```

Expected: 7 tests PASS.

- [ ] **Step 5: Run parser smoke test for list help**

Run:

```bash
python costctl.py list --help
```

Expected: command exits 0 and prints usage for `costctl list` including `--tag` and `--missing-tag`.

- [ ] **Step 6: Required checkpoint — stop after the `list` command milestone**

Stop and report to the user before continuing. Include:
- implemented: EC2, S3, EBS volume, RDS, and CLI output for `list`
- verification: `pytest tests/test_list.py -v` and `python costctl.py list --help`
- files changed: `commands/list_cmd.py`
- suggested commit message: `Implement list command resource discovery`

---

### Task 4: Implement terminate command

**Files:**
- Modify: `commands/terminate_cmd.py:52-98`
- Test: `tests/test_terminate.py:14-58`

- [ ] **Step 1: Use the existing terminate tests as the TDD contract**

The provided tests are:

```python
@mock_aws
def test_terminate_ec2_with_force(capsys):
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ami = ec2.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]
    iid = ec2.run_instances(ImageId=ami, MinCount=1, MaxCount=1, InstanceType="t3.micro")[
        "Instances"
    ][0]["InstanceId"]
    terminate_run(_args("ec2", iid))
    captured = capsys.readouterr()
    assert "Terminated" in captured.out
    states = {
        i["InstanceId"]: i["State"]["Name"]
        for r in ec2.describe_instances()["Reservations"]
        for i in r["Instances"]
    }
    assert states[iid] in ("shutting-down", "terminated")

@mock_aws
def test_terminate_s3_refuses_nonempty(capsys):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="has-stuff")
    s3.put_object(Bucket="has-stuff", Key="file.txt", Body=b"hello")
    terminate_run(_args("s3", "has-stuff"))
    captured = capsys.readouterr()
    assert "Refusing" in captured.out
    assert "has-stuff" in [b["Name"] for b in s3.list_buckets()["Buckets"]]

@mock_aws
def test_terminate_s3_deletes_empty(capsys):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="empty-bucket")
    terminate_run(_args("s3", "empty-bucket"))
    captured = capsys.readouterr()
    assert "Deleted" in captured.out
    assert "empty-bucket" not in [b["Name"] for b in s3.list_buckets()["Buckets"]]

@mock_aws
def test_terminate_nonexistent_handles_clienterror(capsys):
    terminate_run(_args("ec2", "i-doesnotexist"))
    captured = capsys.readouterr()
    assert "AWS error" in captured.out
```

- [ ] **Step 2: Run one terminate test and verify it fails before implementation**

Run:

```bash
pytest tests/test_terminate.py::test_terminate_ec2_with_force -v
```

Expected: FAIL with `NotImplementedError: TODO: implement run()` or `TODO: implement _terminate_ec2`.

- [ ] **Step 3: Implement all terminate helpers and `run(args)`**

In `commands/terminate_cmd.py`, replace `_terminate_ec2`, `_terminate_rds`, `_terminate_s3`, `_terminate_volume`, and `run(args)` with:

```python
def _terminate_ec2(rid, force):
    """Terminate one EC2 instance after confirmation."""
    if not confirm(f"Terminate EC2 {rid}?", force):
        print("Aborted.")
        return

    boto3.client("ec2").terminate_instances(InstanceIds=[rid])
    print(f"Terminated EC2 {rid}")


def _terminate_rds(rid, force):
    """Stop one RDS instance after confirmation.

    Full delete (delete_db_instance) requires a final snapshot decision —
    out of scope for this challenge. Stop is enough to stop billing.
    """
    if not confirm(f"Stop RDS {rid}?", force):
        print("Aborted.")
        return

    boto3.client("rds").stop_db_instance(DBInstanceIdentifier=rid)
    print(f"Stopped RDS {rid}")


def _terminate_s3(rid, force):
    """Delete one S3 bucket — refuse if it has any objects."""
    s3 = boto3.client("s3")
    count = s3.list_objects_v2(Bucket=rid).get("KeyCount", 0)
    if count:
        print(f"Refusing — bucket {rid} has {count} object(s). Empty it first.")
        return

    if not confirm(f"Delete S3 bucket {rid}?", force):
        print("Aborted.")
        return

    s3.delete_bucket(Bucket=rid)
    print(f"Deleted S3 bucket {rid}")


def _terminate_volume(rid, force):
    """Delete one EBS volume after confirmation."""
    if not confirm(f"Delete volume {rid}?", force):
        print("Aborted.")
        return

    boto3.client("ec2").delete_volume(VolumeId=rid)
    print(f"Deleted volume {rid}")
```

Then replace `run(args)` with:

```python
def run(args):
    """Entry point.

    Args set by argparse:
        args.type   — one of "ec2", "rds", "s3", "volume"
        args.id     — resource identifier
        args.force  — bool, skip confirm if True
    """
    try:
        DISPATCH[args.type](args.id, args.force)
    except ClientError as e:
        error = e.response.get("Error", {})
        code = error.get("Code", "Unknown")
        message = error.get("Message", str(e))
        print(f"AWS error [{code}]: {message}")
```

- [ ] **Step 4: Run terminate tests**

Run:

```bash
pytest tests/test_terminate.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Required checkpoint — stop after the `terminate` command milestone**

Stop and report to the user before continuing. Include:
- implemented: safe EC2, RDS, S3, and EBS volume terminate/delete dispatch with friendly AWS errors
- verification: `pytest tests/test_terminate.py -v`
- files changed: `commands/terminate_cmd.py`
- suggested commit message: `Implement safe terminate command handling`

---

### Task 5: Implement clean command

**Files:**
- Modify: `commands/clean_cmd.py:41-58`
- Test: `tests/test_clean.py:14-77`

- [ ] **Step 1: Use the existing clean tests as the TDD contract**

The provided tests are:

```python
@mock_aws
def test_find_targets_finds_tagged_instance():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ami = ec2.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]
    ec2.run_instances(
        ImageId=ami, MinCount=1, MaxCount=1, InstanceType="t3.micro",
        TagSpecifications=[{"ResourceType": "instance",
                            "Tags": [{"Key": "purpose", "Value": "practice"}]}],
    )
    ec2.run_instances(
        ImageId=ami, MinCount=1, MaxCount=1, InstanceType="t3.micro",
        TagSpecifications=[{"ResourceType": "instance",
                            "Tags": [{"Key": "purpose", "Value": "production"}]}],
    )
    t = _find_targets("purpose", "practice")
    assert len(t["ec2"]) == 1

@mock_aws
def test_clean_dry_run_does_not_delete(capsys):
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ami = ec2.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]
    ec2.run_instances(
        ImageId=ami, MinCount=1, MaxCount=1, InstanceType="t3.micro",
        TagSpecifications=[{"ResourceType": "instance",
                            "Tags": [{"Key": "purpose", "Value": "practice"}]}],
    )
    clean_run(_args("purpose=practice", apply_=False))
    captured = capsys.readouterr()
    assert "dry-run" in captured.out

@mock_aws
def test_clean_apply_terminates(capsys):
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ami = ec2.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]
    iid = ec2.run_instances(
        ImageId=ami, MinCount=1, MaxCount=1, InstanceType="t3.micro",
        TagSpecifications=[{"ResourceType": "instance",
                            "Tags": [{"Key": "purpose", "Value": "practice"}]}],
    )["Instances"][0]["InstanceId"]
    clean_run(_args("purpose=practice", apply_=True))
    captured = capsys.readouterr()
    assert "Terminated" in captured.out

@mock_aws
def test_clean_no_matches(capsys):
    clean_run(_args("purpose=practice", apply_=True))
    captured = capsys.readouterr()
    assert "Nothing to clean" in captured.out
```

- [ ] **Step 2: Run one clean test and verify it fails before implementation**

Run:

```bash
pytest tests/test_clean.py::test_find_targets_finds_tagged_instance -v
```

Expected: FAIL with `NotImplementedError: TODO: implement _find_targets`.

- [ ] **Step 3: Update imports**

In `commands/clean_cmd.py`, replace the helper import with:

```python
from commands._common import parse_kv, tags_to_dict
```

- [ ] **Step 4: Implement `_find_targets`**

In `commands/clean_cmd.py`, replace `_find_targets` with:

```python
def _find_targets(tag_key, tag_val):
    """Return {"ec2": [...], "volume": [...]} matching tag in non-terminal state."""
    ec2 = boto3.client("ec2")
    targets = {"ec2": [], "volume": []}

    instance_paginator = ec2.get_paginator("describe_instances")
    for page in instance_paginator.paginate():
        for reservation in page.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                state = instance.get("State", {}).get("Name", "")
                tags = tags_to_dict(instance.get("Tags", []))
                if state not in ("shutting-down", "terminated") and tags.get(tag_key) == tag_val:
                    targets["ec2"].append(instance["InstanceId"])

    volume_paginator = ec2.get_paginator("describe_volumes")
    for page in volume_paginator.paginate():
        for volume in page.get("Volumes", []):
            tags = tags_to_dict(volume.get("Tags", []))
            if volume.get("State") == "available" and tags.get(tag_key) == tag_val:
                targets["volume"].append(volume["VolumeId"])

    return targets
```

- [ ] **Step 5: Implement `run(args)`**

In `commands/clean_cmd.py`, replace `run(args)` with:

```python
def run(args):
    """Entry point.

    Args set by argparse:
        args.tag    — "key=value" string (REQUIRED)
        args.apply  — bool, must be True to actually delete (default False = dry-run)
    """
    tag_key, tag_val = parse_kv(args.tag)
    targets = _find_targets(tag_key, tag_val)

    if not targets["ec2"] and not targets["volume"]:
        print("Nothing to clean.")
        return

    print(f"Deletion plan for {tag_key}={tag_val}:")
    print(f"  EC2 instances: {', '.join(targets['ec2']) if targets['ec2'] else '-'}")
    print(f"  Volumes: {', '.join(targets['volume']) if targets['volume'] else '-'}")

    if not args.apply:
        print("(dry-run — pass --apply to terminate/delete these resources)")
        return

    ec2 = boto3.client("ec2")
    if targets["ec2"]:
        ec2.terminate_instances(InstanceIds=targets["ec2"])
        print(f"Terminated {len(targets['ec2'])} EC2 instance(s): {', '.join(targets['ec2'])}")

    for volume_id in targets["volume"]:
        ec2.delete_volume(VolumeId=volume_id)
        print(f"Deleted volume {volume_id}")
```

- [ ] **Step 6: Run clean tests**

Run:

```bash
pytest tests/test_clean.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 7: Run the automation-backed command tests together**

Run:

```bash
pytest tests/test_list.py tests/test_terminate.py tests/test_clean.py -v
```

Expected: 15 command tests PASS.

- [ ] **Step 8: Required checkpoint — stop after the `clean` command milestone**

Stop and report to the user before continuing. Include:
- implemented: tag-based cleanup discovery, dry-run plan output, and `--apply` termination/deletion
- verification: `pytest tests/test_clean.py -v` and `pytest tests/test_list.py tests/test_terminate.py tests/test_clean.py -v`
- files changed: `commands/clean_cmd.py`
- suggested commit message: `Implement dry-run clean resource cleanup`

---

### Task 6: Implement manual-only tag command

**Files:**
- Modify: `commands/tag_cmd.py:44-86`
- Manual Test: `python costctl.py tag --help`; real AWS verification only when credentials and safe disposable resources are available.

- [ ] **Step 1: Confirm tag command has no provided automated test**

Run:

```bash
python costctl.py tag --help
```

Expected: command exits 0 and prints usage for `costctl tag`, including `--id` and `--set`.

- [ ] **Step 2: Update imports**

In `commands/tag_cmd.py`, replace the import block with:

```python
import boto3
from botocore.exceptions import ClientError

from commands._common import parse_kv, tags_to_dict
```

- [ ] **Step 3: Implement `_to_tags`, EC2, RDS, S3, and volume tag helpers**

In `commands/tag_cmd.py`, replace `_to_tags`, `_tag_ec2`, `_tag_rds`, `_tag_s3`, and `_tag_volume` with:

```python
def _to_tags(set_args):
    """Convert ['k1=v1', 'k2=v2'] to [{'Key':'k1','Value':'v1'}, ...]."""
    return [{"Key": key, "Value": value} for key, value in (parse_kv(item) for item in set_args)]


def _tag_ec2(rid, tags):
    boto3.client("ec2").create_tags(Resources=[rid], Tags=tags)


def _tag_rds(rid, tags):
    rds = boto3.client("rds")
    db = rds.describe_db_instances(DBInstanceIdentifier=rid)["DBInstances"][0]
    rds.add_tags_to_resource(ResourceName=db["DBInstanceArn"], Tags=tags)


def _tag_s3(rid, tags):
    s3 = boto3.client("s3")
    try:
        existing = tags_to_dict(s3.get_bucket_tagging(Bucket=rid).get("TagSet", []))
    except ClientError:
        existing = {}

    for tag in tags:
        existing[tag["Key"]] = tag["Value"]

    tag_set = [{"Key": key, "Value": value} for key, value in sorted(existing.items())]
    s3.put_bucket_tagging(Bucket=rid, Tagging={"TagSet": tag_set})


def _tag_volume(rid, tags):
    boto3.client("ec2").create_tags(Resources=[rid], Tags=tags)
```

- [ ] **Step 4: Implement `run(args)`**

In `commands/tag_cmd.py`, replace `run(args)` with:

```python
def run(args):
    """Entry point.

    Args set by argparse:
        args.type  — one of "ec2", "rds", "s3", "volume"
        args.id    — resource identifier
        args.set   — list[str], each "key=value"
    """
    tags = _to_tags(args.set)
    DISPATCH[args.type](args.id, tags)
    summary = ", ".join(f"{tag['Key']}={tag['Value']}" for tag in tags)
    print(f"Applied {len(tags)} tag(s) to {args.type} {args.id}: {summary}")
```

- [ ] **Step 5: Run parser smoke test again**

Run:

```bash
python costctl.py tag --help
```

Expected: command exits 0 and prints usage for `costctl tag`, including `--id` and `--set`.

- [ ] **Step 6: Run the full automated suite to ensure manual tag work did not regress tested commands**

Run:

```bash
make test
```

Expected: 25 tests PASS.

- [ ] **Step 7: Manually verify tag command only if AWS credentials and a safe resource are available**

Run only when using a real AWS account with a safe disposable resource:

```bash
./costctl.py tag ec2 --id <real-instance-id> --set Owner=alice
./costctl.py list ec2 --tag Owner=alice
```

Expected: the resource tagged with `Owner=alice` appears in the list output.

If AWS credentials or safe resources are not available, record that manual tag verification is pending user execution and do not claim it was verified against AWS.

- [ ] **Step 8: Required checkpoint — stop after the `tag` command milestone**

Stop and report to the user before continuing. Include:
- implemented: EC2, RDS, S3, and EBS volume tag application, including S3 tag merge behavior
- verification: `python costctl.py tag --help`, `make test`, and either real AWS tag/list verification or a note that manual AWS verification is pending user execution
- files changed: `commands/tag_cmd.py`
- suggested commit message: `Implement tag command for AWS resources`

---

### Task 7: Update README submission-facing naming

**Files:**
- Modify: `README.md:1-312`
- Test: read-only text verification with `grep` or manual search.

- [ ] **Step 1: Inspect current placeholder lines**

Check these README sections before editing:

```markdown
# costctl — XBrain W6 side challenge starter

A starter scaffold for a small AWS-resource-management CLI. **The CLI structure
is built; you implement the command logic.** Fork this repo, fill in the
stubs, make the tests pass, customize for your group, then submit.
```

```markdown
git clone <your-fork-url> g<N>-costctl && cd g<N>-costctl
```

```markdown
- [ ] Fork → rename to `g<N>-costctl` → clone locally
- [ ] `make test` final score reported in README (e.g. "21/25 passing")
- [ ] Replace `g<N>` placeholders throughout README with your real group number
- [ ] Add Name section for the individual submission
```

```markdown
## Name

> Replace before submission:

- Vinh
```

- [ ] **Step 2: Update the opening description**

Replace the opening paragraph with:

```markdown
A starter scaffold for a small AWS-resource-management CLI. **The CLI structure
is built; this Vinh-G6 fork implements the command logic.** Make the tests pass,
keep the implementation scoped to the assignment, then submit.
```

- [ ] **Step 3: Update the quickstart clone directory**

Replace:

```markdown
git clone <your-fork-url> g<N>-costctl && cd g<N>-costctl
```

With:

```markdown
git clone <your-fork-url> Vinh-G6-costctl && cd Vinh-G6-costctl
```

- [ ] **Step 4: Update the submission checklist**

Replace the submission checklist block with:

```markdown
- [ ] Fork → rename to `Vinh-G6-costctl` → clone locally
- [ ] `make install-dev && make test` shows 10 passed at start
- [ ] Implement `list` → `pytest tests/test_list.py` all green (7 more pass)
- [ ] Implement `terminate` and `tag`
- [ ] Implement stretch `clean` → `pytest tests/test_clean.py` green
- [ ] `make test` final score reported in README: `25/25 passing`
- [ ] Replace `sample_output/*_example.txt` with real outputs from your account if AWS credentials and safe resources are available
- [ ] `REFLECTIONS.md` with 2+ answers
- [ ] At least 3 meaningful commits (init → first command working → final polish)
- [ ] Submission naming uses `Vinh-G6` throughout README
- [ ] Name section identifies `Vinh`
- [ ] Tag: `git tag w6-sidechallenge-v1 && git push --tags`
```

- [ ] **Step 5: Update the Name section**

Replace the Team section with an individual Name section:

```markdown
## Name

- Vinh
```

- [ ] **Step 6: Add final score note near initial state**

After this existing block:

```markdown
**Initial state of `make test`:** 10 passed (helpers), 15 failed (commands).
You're done when all 25 pass.
```

Add:

```markdown
**Final target for this Vinh-G6 implementation:** `25/25` passing tests.
```

- [ ] **Step 7: Verify no generic group placeholders remain in README**

Run:

```bash
grep -n "g<N>\|G<N>\|<name\|Team\|Slack\|#w6-sidechallenge" README.md
```

Expected: no output.

- [ ] **Step 8: Required checkpoint — stop after the README/submission documentation milestone**

Stop and report to the user before continuing. Include:
- implemented: Vinh-G6 naming, final-score wording, Name section, Slack requirement removal, and honest sample-output wording
- verification: `grep -n "g<N>\|G<N>\|<name" README.md` has no output
- files changed: `README.md`
- suggested commit message: `Update Vinh-G6 submission documentation`

---

### Task 8: Final verification and sample-output decision

**Files:**
- Verify: `commands/list_cmd.py`
- Verify: `commands/terminate_cmd.py`
- Verify: `commands/clean_cmd.py`
- Verify: `commands/tag_cmd.py`
- Verify: `README.md`
- Optional Modify: `sample_output/*` only with real AWS output.

- [ ] **Step 1: Run list tests**

Run:

```bash
pytest tests/test_list.py -v
```

Expected: 7 tests PASS.

- [ ] **Step 2: Run terminate tests**

Run:

```bash
pytest tests/test_terminate.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 3: Run clean tests**

Run:

```bash
pytest tests/test_clean.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 4: Run full suite**

Run:

```bash
make test
```

Expected: 25 tests PASS.

- [ ] **Step 5: Run CLI help smoke tests**

Run:

```bash
python costctl.py --help
python costctl.py list --help
python costctl.py terminate --help
python costctl.py tag --help
python costctl.py clean --help
```

Expected: each command exits 0 and prints usage text.

- [ ] **Step 6: Decide sample-output handling honestly**

If AWS credentials and safe disposable resources are available, run representative commands and replace sample files with real output:

```bash
./costctl.py list ec2
./costctl.py list s3
./costctl.py clean --tag purpose=practice
```

Expected: commands produce real account output suitable for `sample_output/`.

If AWS credentials or safe resources are not available, do not modify `sample_output/`; document in the final response that sample-output replacement and real AWS tag verification are pending user execution.

- [ ] **Step 7: Check working tree**

Run:

```bash
git status --short
```

Expected: changed files are limited to planned files plus any user-approved real `sample_output/` updates.

- [ ] **Step 8: Required checkpoint — stop after final verification**

Stop and report to the user. Include:
- implemented: no new command work unless final verification required a small meaningful fix
- verification: `pytest tests/test_list.py -v`, `pytest tests/test_terminate.py -v`, `pytest tests/test_clean.py -v`, `make test`, CLI help smoke tests, sample-output decision, and `git status --short`
- files changed: all planned files still modified in the working tree, plus any user-approved real `sample_output/` updates
- suggested commit message: `Complete costctl verification pass`

---

## Self-Review

- Spec coverage: Tasks 1-3 cover `list`; Task 4 covers `terminate`; Task 5 covers `clean`; Task 6 covers `tag`; Task 7 covers README naming and final-score wording; Task 8 covers hard verification and sample-output handling.
- Execution control: The plan requires `superpowers:subagent-driven-development`, fresh Sonnet subagents for implementation phases, inline execution in the current checkout, strict no worktree creation/use, and stop/report checkpoints at every meaningful command or documentation boundary.
- Commit-message style: The plan only asks for concise suggested commit messages and does not include Claude co-author trailers.
- Placeholder scan: The plan contains no implementation placeholders. `<real-instance-id>` and `<repo-url>` appear only in manual user-supplied command examples where real external values are required.
- Type consistency: All command helpers use existing signatures from the stub files; `run(args)` functions use the exact argparse fields from `costctl.py`; tag dictionaries use boto3 `{"Key": ..., "Value": ...}` shape throughout.
