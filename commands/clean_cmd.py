"""clean — (stretch) bulk terminate resources matching a tag.

WARNING — DESIGN-FOR-SAFETY
---------------------------
This is the most dangerous command in the CLI. Get the contract right:

  1. DEFAULT IS DRY-RUN. Without --apply the command MUST NOT touch resources.
     It only lists what WOULD be deleted.
  2. Even with --apply, you should consider printing a summary count first
     ("about to terminate N EC2 + M volumes — proceed?"), though for this
     starter a hard `--apply` flag is enough.
  3. Never use this with a tag you don't fully own. Reflection prompt in
     README covers the blast-radius scenario.

WHAT YOU MUST BUILD
-------------------
1. `_find_targets(tag_key, tag_val)` — return a dict like:
     {"ec2": [<instance ids in non-terminal state>],
      "volume": [<volume ids in 'available' state only>]}
   Skip terminated/shutting-down instances (already gone).
   Skip in-use volumes (can't delete while attached — would error anyway).

2. `run(args)` — call _find_targets, print the plan, then either:
     - bail with "(dry-run — pass --apply to ...)"  (default)
     - or actually terminate (when --apply)

HELPERS YOU CAN USE
-------------------
From commands._common:
  parse_kv(s) -> (k, v)

AWS APIS YOU'LL NEED
--------------------
- ec2.describe_instances() + describe_volumes() — same as list_cmd
- ec2.terminate_instances(InstanceIds=[...])
- ec2.delete_volume(VolumeId=...)  (per volume, no bulk API)

VERIFY
------
    pytest tests/test_clean.py -v
"""
import boto3

from commands._common import parse_kv, tags_to_dict


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
