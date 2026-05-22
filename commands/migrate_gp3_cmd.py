"""migrate-gp3 — (stretch) plan or apply gp2 → gp3 EBS migration.

WHY THIS MATTERS
----------------
gp3 is cheaper than gp2 ($0.08 vs $0.10 per GB-month) AND faster
(3000 IOPS baseline vs 3 IOPS/GB scaling). Most gp2 volumes should migrate.
EBS supports live modification — no downtime, no detach.

WHAT YOU MUST BUILD
-------------------
1. Dry-run mode (default):
   - List all gp2 volumes in the account
   - Show size, attached instance, and projected monthly savings per volume
   - Print total savings if all migrated

2. Apply mode (--apply):
   - With --volume-id: migrate just that one
   - Without --volume-id: migrate ALL gp2 volumes
   - Use ec2.modify_volume(...) — the modification runs in the background

AWS APIS YOU'LL NEED
--------------------
ec2.describe_volumes(Filters=[{"Name": "volume-type", "Values": ["gp2"]}])
ec2.modify_volume(
    VolumeId=vid,
    VolumeType="gp3",
    Iops=3000,        # baseline included free
    Throughput=125,   # baseline included free
)

After calling modify_volume, the volume goes through state transitions:
    in-use → modifying → optimizing → in-use (now gp3)
The app stays online throughout. Optimization takes ~30 min for a 100GB
volume; longer for larger volumes.

EXPECTED OUTPUT FORMAT (dry-run)
--------------------------------
    gp2 volumes (price delta $0.020/GB-month):
    ------------------------------------------------------------------------------
      vol-0abc123def456789a    100GB  attached=i-0aaa            $2.00/mo savings
      vol-0bbb456ef789012345     50GB  attached=(none)            $1.00/mo savings
    ------------------------------------------------------------------------------

    (dry-run — pass --apply --volume-id <id> to migrate one, or --apply to migrate ALL)

EXPECTED OUTPUT FORMAT (apply)
------------------------------
      → modify_volume issued for vol-0abc123def456789a (gp3, 3000 IOPS, 125 MiB/s)

    Volume(s) entering 'modifying' → 'optimizing' state. App stays online.
    Use `costctl list volume` after ~30 minutes to confirm 'in-use' + gp3.

VERIFY MANUALLY (no test file for this command)
-----------------------------------------------
    ./costctl.py migrate-gp3                           # dry-run, no side effects
    ./costctl.py migrate-gp3 --apply --volume-id vol-xxx  # migrate ONE

Pick a small volume first. Confirm via:
    ./costctl.py list volume --tag <something>
or AWS Console → EC2 → Volumes.

PRICING NOTE
------------
Constants below assume us-east-1 on-demand pricing. If your account is in
a different region, the dollar figure displayed is rough — but the migration
itself works the same anywhere.
"""
import boto3

# us-east-1 on-demand pricing per GB-month. Override if you care about exact $.
GP2_PRICE = 0.10
GP3_PRICE = 0.08


def _list_gp2_volumes():
    ec2 = boto3.client("ec2")
    volumes = []
    paginator = ec2.get_paginator("describe_volumes")

    for page in paginator.paginate(Filters=[{"Name": "volume-type", "Values": ["gp2"]}]):
        for volume in page.get("Volumes", []):
            attachment = volume.get("Attachments", [])
            attached = attachment[0].get("InstanceId") if attachment else "(none)"
            savings = volume.get("Size", 0) * (GP2_PRICE - GP3_PRICE)
            volumes.append({
                "id": volume["VolumeId"],
                "size_gb": volume.get("Size", 0),
                "attached": attached,
                "monthly_savings": savings,
            })

    return volumes


def _print_dry_run(volumes):
    print("gp2 volumes (price delta $0.020/GB-month):")
    print("-" * 78)
    total_savings = 0.0
    for volume in volumes:
        total_savings += volume["monthly_savings"]
        print(
            f"  {volume['id']:<24} {volume['size_gb']:>5}GB  "
            f"attached={volume['attached']:<18} ${volume['monthly_savings']:.2f}/mo savings"
        )
    print("-" * 78)
    print(f"Total savings: ${total_savings:.2f}/mo")
    print()
    print("(dry-run — pass --apply --volume-id <id> to migrate one, or --apply to migrate ALL)")


def _find_volume(volume_id):
    ec2 = boto3.client("ec2")
    paginator = ec2.get_paginator("describe_volumes")

    for page in paginator.paginate():
        for volume in page.get("Volumes", []):
            if volume["VolumeId"] == volume_id:
                return volume

    return None


def _apply_migration(volume_ids):
    ec2 = boto3.client("ec2")

    if not volume_ids:
        volume_ids = [volume["id"] for volume in _list_gp2_volumes()]
        if not volume_ids:
            print("Nothing to migrate.")
            return

    migrated = 0
    for volume_id in volume_ids:
        volume = _find_volume(volume_id)
        if not volume:
            print(f"Volume {volume_id} not found.")
            continue
        if volume.get("VolumeType") != "gp2":
            print(f"Volume {volume_id} is not gp2; skipping.")
            continue

        ec2.modify_volume(
            VolumeId=volume_id,
            VolumeType="gp3",
            Iops=3000,
            Throughput=125,
        )
        migrated += 1
        print(f"modify_volume issued for {volume_id} (gp3, 3000 IOPS, 125 MiB/s)")

    if migrated:
        print()
        print("Volume(s) entering 'modifying' -> 'optimizing' state. App stays online.")
        print("Use `costctl list volume` after ~30 minutes to confirm 'in-use' + gp3.")


def run(args):
    """Entry point.

    Args set by argparse:
        args.apply       — bool, default False (dry-run)
        args.volume_id   — optional str, only migrate this volume when --apply
    """
    if args.apply:
        volume_ids = [args.volume_id] if args.volume_id else []
        _apply_migration(volume_ids)
        return

    _print_dry_run(_list_gp2_volumes())
