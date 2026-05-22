# Live Read-Only AWS Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename `sample_output/` to `output/`, verify the implemented `costctl` CLI safely against the user's configured AWS account without modifying cloud resources, and store only truthful captured outputs in `output/`.

**Architecture:** Keep the command implementation unchanged unless a repo-facing path still points at `sample_output/`. Use the implemented CLI commands directly against the configured AWS account in read-only ways only: list commands, clean dry-run, and terminate abort paths that exit before any destructive API call. Do not execute `tag` live because it writes tags, and do not execute any `--apply` mode. Capture raw stdout exactly as produced by the CLI so the artifacts match the real account state.

**Tech Stack:** Python 3.14 runtime used in this repo, boto3 via `costctl.py`, configured AWS credentials/profile, Bash, README/Makefile text updates.

---

## File Structure

- Rename: `sample_output/` → `output/`
  - Keep the existing example files only until truthful replacements are captured.
- Modify: `README.md`
  - Rename repo-facing `sample_output/` references to `output/`.
  - Keep the wording that output files must be real AWS captures.
- Modify: `Makefile`
  - Update the sample capture target to write under `output/`.
- Modify after rename: `output/README.md`
  - Rename the heading and example capture commands from `sample_output/` to `output/`.
- Create inside `output/`: live-safe capture files produced by the CLI against the user's account.
- Leave unchanged: `commands/*.py`
  - No new feature work is required for this verification pass.

---

### Task 1: Rename `sample_output/` to `output/` and update repo-facing references

**Files:**
- Rename: `sample_output/` → `output/`
- Modify: `README.md`
- Modify: `Makefile`
- Modify: `output/README.md`

- [ ] **Step 1: Verify the current directory contains `sample_output/` before renaming**

Run:

```bash
ls
```

Expected: the repository root is listed and `sample_output` appears in the output.

- [ ] **Step 2: Rename the directory**

Run:

```bash
mv sample_output output
```

Expected: `sample_output/` no longer exists and `output/` exists.

- [ ] **Step 3: Update `README.md` repo-facing references**

The resulting `README.md` snippets must read exactly like this:

```markdown
| `output/*_example.txt` | Replace with REAL outputs once your impl works |
```

```markdown
├── output/                   # example outputs — replace with yours
```

```markdown
- [ ] Replace `output/*_example.txt` only with real AWS output if safe credentials and disposable resources are available
```

- [ ] **Step 4: Update the sample capture target in `Makefile`**

The resulting `Makefile` snippet must read exactly like this:

```make
sample-output:
	./costctl.py list ec2 > output/list_ec2_$$(date +%F).txt
	@echo "Wrote output/list_ec2_$$(date +%F).txt"
```

- [ ] **Step 5: Update `output/README.md` after the rename**

Replace the file contents with this exact text:

```markdown
# output/

These files are **illustrative examples** showing the shape of `costctl`
output. They are NOT real account data.

When you submit, replace each `*_example.txt` with a real output from running
`costctl` against your workshop account. Then delete the example files.

## How to produce real samples

```bash
./costctl.py list ec2 > output/list_ec2_$(date +%F).txt
./costctl.py list ec2 --missing-tag Application > output/list_ec2_missing_app_$(date +%F).txt
./costctl.py cost --tag Application=<your-app> --days 7 > output/cost_<your-app>_$(date +%F).txt
```

The trainer will `git clone` your repo, follow the README, and expect to
reproduce roughly these outputs (allowing for natural drift in timestamps and
resource lists between snapshots).

## Anti-pattern

Don't paste fabricated output. If `costctl list ec2` against your account
returns 0 rows, commit that — it's a valid output. Don't invent fake instance
IDs to make the sample look "interesting".
```

- [ ] **Step 6: Verify repo-facing path updates are complete**

Run:

```bash
grep -n "sample_output\|output/" README.md Makefile output/README.md
```

Expected: `README.md`, `Makefile`, and `output/README.md` show only the intended `output/` references and no remaining `sample_output/` lines.

---

### Task 2: Establish the live-safe command matrix before contacting AWS

**Files:**
- Read only: `costctl.py`
- Read only: `commands/list_cmd.py`
- Read only: `commands/clean_cmd.py`
- Read only: `commands/terminate_cmd.py`
- Read only: `commands/tag_cmd.py`
- Read only: `commands/cost_cmd.py`
- Read only: `commands/idle_cmd.py`
- Read only: `commands/migrate_gp3_cmd.py`

- [ ] **Step 1: Confirm which commands are implemented and which are safe to run live**

Use this exact matrix during execution:

```text
list           -> SAFE live execution (read-only AWS APIs)
clean          -> SAFE only without --apply (dry-run only)
terminate      -> SAFE only through an abort path that returns before the write API call
tag            -> DO NOT run live (writes tags immediately)
cost           -> currently stubbed; only --help is truthful
idle           -> currently stubbed; only --help is truthful
migrate-gp3    -> currently stubbed; only --help is truthful
```

- [ ] **Step 2: Resolve the actual AWS region instead of assuming `us-east-1`**

`costctl.py` defaults `--region` to `us-east-1` unless `AWS_REGION` or `AWS_DEFAULT_REGION` is already set, so read the configured CLI region first.

Run:

```bash
aws configure get region
```

Expected: a region string such as `ap-southeast-1` or `us-east-1`.

- [ ] **Step 3: Verify the configured credentials can read the target account**

Run:

```bash
aws sts get-caller-identity
```

Expected: JSON with `Account`, `Arn`, and `UserId`.

- [ ] **Step 4: Smoke-test help output for the full CLI surface**

Run:

```bash
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --help
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" list --help
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" terminate --help
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" tag --help
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" clean --help
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" cost --help
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" idle --help
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" migrate-gp3 --help
```

Expected: all help commands exit cleanly.

---

### Task 3: Discover representative live resources using read-only commands

**Files:**
- Create: `output/list_ec2_<date>.txt`
- Create: `output/list_ec2_missing_app_<date>.txt`
- Create: `output/list_s3_<date>.txt`
- Create: `output/list_rds_<date>.txt`
- Create: `output/list_volume_<date>.txt`

- [ ] **Step 1: Capture the implemented list commands against the configured region**

Replace `<region>` with the exact string returned by `aws configure get region`, then run:

```bash
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> list ec2
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> list ec2 --missing-tag Application
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> list s3
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> list rds
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> list volume
```

Expected: each command prints a table with `N found`, even when `N` is `0`.

- [ ] **Step 2: Persist the raw list outputs exactly as produced**

Run the same commands again with redirection:

```bash
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> list ec2 > output/list_ec2_$(date +%F).txt
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> list ec2 --missing-tag Application > output/list_ec2_missing_app_$(date +%F).txt
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> list s3 > output/list_s3_$(date +%F).txt
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> list rds > output/list_rds_$(date +%F).txt
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> list volume > output/list_volume_$(date +%F).txt
```

Expected: the files contain the exact stdout from the live commands.

- [ ] **Step 3: Choose a safe dry-run tag for `clean`**

Use this rule exactly:

```text
If the first EC2 row contains at least one tag pair, use the first visible key=value pair from that row.
Else if the first EBS volume row contains at least one tag pair, use the first visible key=value pair from that row.
Else run clean with the sentinel tag __no_match__=__no_match__ and expect "Nothing to clean."
```

- [ ] **Step 4: Choose a safe abort target for `terminate`**

Use this rule exactly:

```text
Prefer a real EC2 instance id from the live list output.
If no EC2 instance exists, use a real EBS volume id.
If no EBS volume exists, use a real RDS identifier.
If none of those exist, do not run terminate live and document that no safe real target existed.
```

---

### Task 4: Capture safe non-destructive command outputs and explicitly skip write paths

**Files:**
- Create: `output/clean_dry_run_<date>.txt`
- Create: `output/terminate_abort_<type>_<date>.txt` when a safe target exists
- Create: `output/help_<command>_<date>.txt` for non-implemented or write-only commands

- [ ] **Step 1: Capture `clean` dry-run output**

If Task 3 selected a real tag `key=value`, run:

```bash
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> clean --tag key=value > output/clean_dry_run_$(date +%F).txt
```

If Task 3 selected the sentinel tag, run:

```bash
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> clean --tag __no_match__=__no_match__ > output/clean_dry_run_$(date +%F).txt
```

Expected: either a deletion plan plus the dry-run reminder, or `Nothing to clean.`

- [ ] **Step 2: Capture a safe terminate abort output when a real target exists**

If Task 3 selected an EC2 id, run:

```bash
printf 'n\n' | "C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> terminate ec2 --id <real-ec2-id> > output/terminate_abort_ec2_$(date +%F).txt
```

If Task 3 selected a volume id, run:

```bash
printf 'n\n' | "C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> terminate volume --id <real-volume-id> > output/terminate_abort_volume_$(date +%F).txt
```

If Task 3 selected an RDS identifier, run:

```bash
printf 'n\n' | "C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" --region <region> terminate rds --id <real-rds-id> > output/terminate_abort_rds_$(date +%F).txt
```

Expected: `Aborted.` and no destructive API call.

- [ ] **Step 3: Capture help output for commands that cannot be truthfully run live in read-only mode**

Run:

```bash
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" tag --help > output/help_tag_$(date +%F).txt
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" cost --help > output/help_cost_$(date +%F).txt
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" idle --help > output/help_idle_$(date +%F).txt
"C:/Python314/python.exe" "C:/Users/thanh/Desktop/workspace/xbrain-courses/Vinh-G6-costctl/costctl.py" migrate-gp3 --help > output/help_migrate_gp3_$(date +%F).txt
```

Expected: the files are truthful command outputs without issuing any write API call.

- [ ] **Step 4: Explicitly skip write paths**

Do not run any of these live commands:

```text
./costctl.py tag ...
./costctl.py terminate ... --force
./costctl.py clean --apply ...
./costctl.py migrate-gp3 --apply ...
```

Expected: the final report explains that these paths were intentionally not executed because the user requested read-only inspection only.

---

### Task 5: Final verification for the local rename plus live capture set

**Files:**
- Verify: `README.md`
- Verify: `Makefile`
- Verify: `output/README.md`
- Verify: files created in `output/`

- [ ] **Step 1: Run the automated test suite after the local path rename**

Run:

```bash
"C:/Python314/python.exe" -m pytest -v tests/
```

Expected: `25 passed`.

- [ ] **Step 2: Read the generated output files to verify they contain real CLI output**

Run:

```bash
ls output
```

Then read each newly created file and confirm the content matches the command that created it.

Expected: every created file contains raw CLI stdout from the live run; no fabricated prose is inserted.

- [ ] **Step 3: Review the final working tree**

Run:

```bash
git status --short
```

Expected: changes are limited to the rename, the repo-facing reference updates, and the newly captured `output/` files.

- [ ] **Step 4: Final reporting requirements**

The completion report must state all of the following:

```text
- which live commands were run safely against the user's configured account
- which commands were intentionally not run because they would modify resources
- which commands are still stubs and therefore only had help output captured
- which files were created under output/
- whether pytest still reports 25/25 passing tests after the path rename
```
