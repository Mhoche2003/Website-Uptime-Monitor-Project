# This lambda reads the history in DynamoDB and writes the dashboard numbers in metrics.json. 
# We put known rows in the fake table, freeze the date then check the numbers written in the fake bucket.
# Same goes for the three precedent lambda check

import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from moto import mock_aws

from fake_aws import prepare_fake_aws, load_lambda

# "Now" is for the Lambda so 2 October, the month starts on 1 October
FAKE_NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


def add_row(table, check_type, timestamp, success, response_time=1):
    table.put_item(Item={
        "check_type": check_type,
        "timestamp": timestamp,
        "success": success,
        "response_time": Decimal(str(response_time)),
        "error_message": "",
    })


def run_lambda(lambda_function):
    # Freeze the date, then read metrics.json from the fake bucket
    with patch.object(lambda_function, "datetime") as fake_datetime:
        fake_datetime.now.return_value = FAKE_NOW
        lambda_function.lambda_handler({}, None)


def read_metrics(s3):
    file = s3.get_object(Bucket="test-bucket", Key="metrics.json")
    return json.loads(file["Body"].read())


@mock_aws
def test_month_with_rows():
    table, sqs, queue_url, s3 = prepare_fake_aws()
    lambda_function = load_lambda("aggregate_metrics")

    # Creathe the 4 availability checks, 1 failed: 3/4 = 75%
    add_row(table, "availability", "2026-10-01T02:00:00+00:00", True)
    add_row(table, "availability", "2026-10-01T08:00:00+00:00", True)
    add_row(table, "availability", "2026-10-01T14:00:00+00:00", False)
    add_row(table, "availability", "2026-10-02T09:00:00+00:00", True)
    # 2 latency checks, 1s and 3s: average 2s
    add_row(table, "latency", "2026-10-01T02:00:00+00:00", True, 1)
    add_row(table, "latency", "2026-10-01T08:00:00+00:00", True, 3)
    # 2 content checks, no failure
    add_row(table, "content", "2026-10-01T02:00:00+00:00", True)
    add_row(table, "content", "2026-10-01T08:00:00+00:00", True)

    run_lambda(lambda_function)
    metrics = read_metrics(s3)

    assert metrics["availability_percent"] == 75
    assert metrics["average_response_time_seconds"] == 2
    assert metrics["failures_by_check"] == {"availability": 1, "latency": 0, "content": 0}
    assert metrics["total_checks_by_check"] == {"availability": 4, "latency": 2, "content": 2}


@mock_aws
def test_empty_month():
    table, sqs, queue_url, s3 = prepare_fake_aws()
    lambda_function = load_lambda("aggregate_metrics")

    # No row at all: the Lambda must not divide by zero !
    run_lambda(lambda_function)
    metrics = read_metrics(s3)

    assert metrics["availability_percent"] == 0
    assert metrics["average_response_time_seconds"] == 0
    assert metrics["total_checks_by_check"] == {"availability": 0, "latency": 0, "content": 0}


@mock_aws
def test_previous_month_is_ignored():
    table, sqs, queue_url, s3 = prepare_fake_aws()
    lambda_function = load_lambda("aggregate_metrics")

    # A failure in September must not count in October. (Separte by mounths only)
    add_row(table, "availability", "2026-09-20T10:00:00+00:00", False)
    add_row(table, "availability", "2026-10-01T10:00:00+00:00", True)

    run_lambda(lambda_function)
    metrics = read_metrics(s3)

    assert metrics["total_checks_by_check"]["availability"] == 1
    assert metrics["availability_percent"] == 100
