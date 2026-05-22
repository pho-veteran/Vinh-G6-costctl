"""Tests for idle_cmd CPU classification and output."""
from types import SimpleNamespace

import boto3
from moto import mock_aws

from commands.idle_cmd import _avg_cpu, run as idle_run


class _FakeCloudWatch:
    def __init__(self, datapoints):
        self.datapoints = datapoints
        self.calls = []

    def get_metric_statistics(self, **kwargs):
        self.calls.append(kwargs)
        return {"Datapoints": self.datapoints}


class _Args(SimpleNamespace):
    pass


def test_avg_cpu_returns_mean_and_uses_expected_cloudwatch_request():
    cw = _FakeCloudWatch([
        {"Average": 12.0},
        {"Average": 6.0},
        {"Average": 3.0},
    ])

    result = _avg_cpu(cw, "i-123", 24)

    assert result == 7.0
    assert len(cw.calls) == 1
    call = cw.calls[0]
    assert call["Namespace"] == "AWS/EC2"
    assert call["MetricName"] == "CPUUtilization"
    assert call["Dimensions"] == [{"Name": "InstanceId", "Value": "i-123"}]
    assert call["Period"] == 3600
    assert call["Statistics"] == ["Average"]
    assert call["EndTime"] > call["StartTime"]


def test_avg_cpu_returns_none_when_cloudwatch_has_no_datapoints():
    cw = _FakeCloudWatch([])

    result = _avg_cpu(cw, "i-123", 24)

    assert result is None


@mock_aws
def test_idle_run_prints_skip_idle_active_and_no_data_rows(capsys, monkeypatch):
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ami = ec2.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]

    instances = []
    instances.append(
        ec2.run_instances(
            ImageId=ami,
            MinCount=1,
            MaxCount=1,
            InstanceType="t3.micro",
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [{"Key": "keep", "Value": "true"}],
            }],
        )["Instances"][0]["InstanceId"]
    )
    instances.append(
        ec2.run_instances(
            ImageId=ami,
            MinCount=1,
            MaxCount=1,
            InstanceType="t3.small",
        )["Instances"][0]["InstanceId"]
    )
    instances.append(
        ec2.run_instances(
            ImageId=ami,
            MinCount=1,
            MaxCount=1,
            InstanceType="t3.nano",
        )["Instances"][0]["InstanceId"]
    )
    instances.append(
        ec2.run_instances(
            ImageId=ami,
            MinCount=1,
            MaxCount=1,
            InstanceType="t3.medium",
        )["Instances"][0]["InstanceId"]
    )

    averages = {
        instances[1]: 1.2,
        instances[2]: 42.5,
        instances[3]: None,
    }

    def fake_avg_cpu(_cw, instance_id, hours):
        assert hours == 24
        return averages[instance_id]

    monkeypatch.setattr("commands.idle_cmd._avg_cpu", fake_avg_cpu)

    idle_run(_Args(threshold=5.0, hours=24))
    captured = capsys.readouterr()

    assert "Scanning running EC2 (excluding keep=true) - threshold 5.0% over 24h:" in captured.out
    assert "SKIP keep=true" in captured.out
    assert "cpu_24h= 1.20%  <- IDLE" in captured.out
    assert "cpu_24h=42.50%" in captured.out
    assert "cpu_24h=NO DATA" in captured.out
    assert f"Idle: 1 instance(s): ['{instances[1]}']" in captured.out
    assert "Tip: combo with terminate ->  ./costctl.py terminate ec2 --id <id>" in captured.out
