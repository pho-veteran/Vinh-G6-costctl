"""Tests for migrate_gp3_cmd dry-run and apply behaviour."""
import io
import sys
from types import SimpleNamespace

import boto3
from moto import mock_aws

from commands.migrate_gp3_cmd import run as migrate_run


def _args(apply_=False, volume_id=None):
    return SimpleNamespace(apply=apply_, volume_id=volume_id)


@mock_aws
def test_migrate_gp3_dry_run_lists_gp2_volumes_and_total_savings(capsys):
    ec2 = boto3.client("ec2", region_name="us-east-1")
    gp2 = ec2.create_volume(Size=100, VolumeType="gp2", AvailabilityZone="us-east-1a")
    ec2.create_volume(Size=50, VolumeType="gp3", AvailabilityZone="us-east-1a")

    migrate_run(_args(apply_=False))

    captured = capsys.readouterr()
    assert gp2["VolumeId"] in captured.out
    assert "$2.00/mo savings" in captured.out
    assert "Total savings: $2.00/mo" in captured.out
    assert "dry-run" in captured.out


@mock_aws
def test_migrate_gp3_dry_run_empty_shows_zero_total(capsys):
    migrate_run(_args(apply_=False))

    captured = capsys.readouterr()
    assert "gp2 volumes" in captured.out
    assert "Total savings: $0.00/mo" in captured.out
    assert "dry-run" in captured.out


@mock_aws
def test_migrate_gp3_apply_volume_id_modifies_one_gp2_volume(capsys):
    ec2 = boto3.client("ec2", region_name="us-east-1")
    gp2 = ec2.create_volume(Size=10, VolumeType="gp2", AvailabilityZone="us-east-1a")
    gp2_other = ec2.create_volume(Size=20, VolumeType="gp2", AvailabilityZone="us-east-1a")

    migrate_run(_args(apply_=True, volume_id=gp2["VolumeId"]))

    captured = capsys.readouterr()
    assert gp2["VolumeId"] in captured.out
    assert gp2_other["VolumeId"] not in captured.out
    assert "modify_volume issued" in captured.out


@mock_aws
def test_migrate_gp3_apply_all_modifies_all_gp2_volumes(capsys):
    ec2 = boto3.client("ec2", region_name="us-east-1")
    gp2_a = ec2.create_volume(Size=10, VolumeType="gp2", AvailabilityZone="us-east-1a")
    gp2_b = ec2.create_volume(Size=20, VolumeType="gp2", AvailabilityZone="us-east-1a")
    gp3 = ec2.create_volume(Size=30, VolumeType="gp3", AvailabilityZone="us-east-1a")

    migrate_run(_args(apply_=True))

    captured = capsys.readouterr()
    assert gp2_a["VolumeId"] in captured.out
    assert gp2_b["VolumeId"] in captured.out
    assert gp3["VolumeId"] not in captured.out
    assert captured.out.count("modify_volume issued") == 2


@mock_aws
def test_migrate_gp3_apply_nothing_to_migrate(capsys):
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ec2.create_volume(Size=10, VolumeType="gp3", AvailabilityZone="us-east-1a")

    migrate_run(_args(apply_=True))

    captured = capsys.readouterr()
    assert "Nothing to migrate" in captured.out


@mock_aws
def test_migrate_gp3_apply_volume_id_skips_non_gp2(capsys):
    ec2 = boto3.client("ec2", region_name="us-east-1")
    gp3 = ec2.create_volume(Size=10, VolumeType="gp3", AvailabilityZone="us-east-1a")

    migrate_run(_args(apply_=True, volume_id=gp3["VolumeId"]))

    captured = capsys.readouterr()
    assert gp3["VolumeId"] in captured.out
    assert "is not gp2" in captured.out
    assert "modify_volume issued" not in captured.out


@mock_aws
def test_migrate_gp3_apply_volume_id_missing(capsys):
    migrate_run(_args(apply_=True, volume_id="vol-does-not-exist"))

    captured = capsys.readouterr()
    assert "vol-does-not-exist" in captured.out
    assert "not found" in captured.out
    assert "modify_volume issued" not in captured.out


@mock_aws
def test_migrate_gp3_apply_reports_modification_status_hint(capsys):
    ec2 = boto3.client("ec2", region_name="us-east-1")
    gp2 = ec2.create_volume(Size=10, VolumeType="gp2", AvailabilityZone="us-east-1a")

    migrate_run(_args(apply_=True, volume_id=gp2["VolumeId"]))

    captured = capsys.readouterr()
    assert "optimizing" in captured.out
    assert "costctl list volume" in captured.out
    assert "App stays online" in captured.out


@mock_aws
def test_migrate_gp3_apply_status_is_cp1252_safe(monkeypatch):
    ec2 = boto3.client("ec2", region_name="us-east-1")
    gp2 = ec2.create_volume(Size=10, VolumeType="gp2", AvailabilityZone="us-east-1a")
    stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", stream)

    migrate_run(_args(apply_=True, volume_id=gp2["VolumeId"]))

    stream.flush()
    output = stream.buffer.getvalue().decode("cp1252")
    assert "modify_volume issued" in output
    assert "optimizing" in output
    assert "App stays online" in output
    assert "->" in output
    assert "→" not in output
    stream.detach()
