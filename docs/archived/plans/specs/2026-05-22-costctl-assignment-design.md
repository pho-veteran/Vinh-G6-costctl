# Costctl Assignment Design

## Goal
Implement the `costctl` starter so the repo reaches `25/25` passing tests, then extend it with one additional core command that is manual-only in this starter, while updating submission-facing naming from group-only placeholders to `Vinh-G6`.

## Scope
This design covers the existing starter repository at `Vinh-G6-costctl`. The repo currently includes automated tests for helper functions, `list`, `terminate`, and `clean`. It does not currently include automated tests for `cost` or `tag`, so those commands are treated as manual-verification scope in this design.

The chosen delivery path is the broad implementation path:
1. Implement `list`.
2. Implement `terminate`.
3. Implement `clean`.
4. Implement one additional core command that verifies manually, with `tag` preferred over `cost` because it is easier to validate directly using the existing `list` command.
5. Update README and submission-facing naming from `g<N>` / `G<N>` or group-only wording to `Vinh-G6` where appropriate.
6. Treat `sample_output/` replacement as a manual artifact: replace only with real AWS output if credentials are available; do not fabricate sample output.

## Constraints
- Keep changes surgical and limited to files directly related to the assignment.
- Use the existing helper functions in `commands/_common.py` instead of rebuilding tag parsing or matching logic.
- Do not change the provided tests unless a parser or repo inconsistency makes that unavoidable, which is not expected from the current repo state.
- Preserve the safety contracts in destructive commands: confirmation by default for `terminate`, and dry-run by default for `clean`.
- Let `costctl.py` and `tests/conftest.py` own region setup through environment variables; command modules can use plain `boto3.client("ec2")`, `boto3.client("s3")`, and `boto3.client("rds")`.

## File-Level Design
### `commands/list_cmd.py`
Implement all four resource listers and the command entrypoint:
- `_list_ec2(want, missing)` using `describe_instances()` pagination and `tags_match(...)`
- `_list_rds(want, missing)` using `describe_db_instances()` and `list_tags_for_resource(...)`; this path is not covered by the provided tests, so implement it from the module docstring and verify manually if possible
- `_list_s3(want, missing)` using `list_buckets()` and `get_bucket_tagging(...)`, treating missing tagging config as empty tags
- `_list_volume(want, missing)` using `describe_volumes()` pagination and the required `<type>-<size>GB` display shape
- `run(args)` to parse `--tag`, pass filters through `DISPATCH`, and print the formatted table contract described in the module docstring

No new shared abstraction is needed beyond tiny local formatting helpers if repetition becomes unavoidable.

### `commands/terminate_cmd.py`
Implement the resource-specific destructive actions and the guarded entrypoint:
- `_terminate_ec2(rid, force)` → confirm unless forced, then terminate instance
- `_terminate_rds(rid, force)` → confirm unless forced, then stop DB instance
- `_terminate_s3(rid, force)` → inspect object count first, refuse non-empty buckets, otherwise confirm and delete
- `_terminate_volume(rid, force)` → confirm unless forced, then delete volume
- `run(args)` → dispatch through `DISPATCH` inside `try/except ClientError` and print the friendly AWS error message shape required by the docstring

This file should keep the error handling centralized in `run(args)` unless a resource-specific message is required by the contract.

### `commands/clean_cmd.py`
Implement the stretch command because it is already part of the automated repo contract:
- `_find_targets(tag_key, tag_val)` returns matching EC2 instance ids in non-terminal states and matching EBS volume ids in `available` state only
- `run(args)` parses the tag, prints a deletion plan, defaults to dry-run, and only performs termination/deletion with `--apply`
- output must preserve the substrings required by the provided tests: dry-run output contains `dry-run`, apply output contains `Terminated`, and no-match output contains `Nothing to clean`

The implementation should directly call the AWS clients needed by the docstring and avoid reusing `terminate_cmd.py` wrappers unless that reuse stays trivial and does not complicate tests.

### `commands/tag_cmd.py`
Implement one manual-only core command after the test-backed commands are green:
- `_to_tags(set_args)` converts repeated `key=value` args into boto3 tag dicts
- `_tag_ec2(rid, tags)` and `_tag_volume(rid, tags)` use EC2 `create_tags(...)`
- `_tag_rds(rid, tags)` resolves the DB ARN first, then calls `add_tags_to_resource(...)`
- `_tag_s3(rid, tags)` reads existing tags, merges them with new values by key, and writes the full merged tagset with `put_bucket_tagging(...)`
- `run(args)` parses `--set`, dispatches by resource type, and prints the applied tag summary

`tag` is preferred over `cost` because it can be verified immediately against existing `list` functionality without depending on billing lag or cost allocation tag activation.

### `README.md`
Update assignment-facing text to reflect the individual submission naming:
- replace clone/repo placeholders like `g<N>-costctl` with `Vinh-G6-costctl`
- replace submission prefix examples like `G<N>` with `Vinh-G6`
- replace the placeholder Team section with a concise Name section for this individual project
- adjust final test-score wording to reflect the target `25/25` passing result once implementation is complete
- keep the original assignment instructions intact where they describe the mentor’s baseline brief, but make this fork’s identity and submission wording clearly individual

If the repo already uses `Vinh-G6` in paths but still contains `G<N>` placeholders in visible text, only those visible placeholders should change.

### `sample_output/`
The README asks for real account outputs before submission. This implementation should not fabricate sample output. If real AWS credentials and resources are available after implementation, replace sample outputs with captured command output; otherwise leave them unchanged and document manual verification as pending user execution.

## Verification Design
### Hard verification gates
1. `pytest tests/test_list.py -v`
2. `pytest tests/test_terminate.py -v`
3. `pytest tests/test_clean.py -v`
4. `make test`

The repository is considered automation-complete only when `make test` reports `25/25` passing.

### Manual verification
After the automated suite is green:
1. Run `./costctl.py tag <type> --id <real-id> --set Owner=alice`
2. Run the corresponding `./costctl.py list <type> --tag Owner=alice`
3. Confirm the resource appears with the expected tag
4. If real AWS credentials and safe disposable resources are available, capture representative outputs for `sample_output/`; otherwise do not modify sample outputs.

If AWS credentials are not configured in this environment, the implementation can still be completed and the manual verification step should be documented as pending user execution.

## Testing Strategy
Follow the repo’s existing TDD-oriented flow file by file:
- start with one failing test from `tests/test_list.py`
- implement the minimum code to satisfy that behavior
- re-run the specific test, then the whole file
- repeat for `terminate`, then `clean`
- only after test-backed work is green, implement `tag` and verify manually

This keeps the high-confidence path first while still satisfying the broader implementation scope selected for this repo.

## Out of Scope
- Adding new tests for `cost` or `tag` unless a very small focused test becomes necessary to safely support the implementation
- Implementing `idle` or `migrate-gp3`
- Refactoring CLI parser structure in `costctl.py` unless a real bug blocks command behavior
- Rewriting the starter README beyond targeted naming, final-score, and submission-facing updates
- Fabricating `sample_output/` files without real AWS command output

## Success Criteria
The work is successful when:
1. `make test` passes with `25/25`.
2. `list`, `terminate`, and `clean` are implemented to the current repo spec.
3. `tag` is implemented and ready for manual verification against a real AWS account.
4. README naming, final-score wording, and submission-facing text use `Vinh-G6` appropriately for this individual version of the assignment.
5. `sample_output/` is either replaced with real AWS output or intentionally left unchanged with manual verification documented as pending.
