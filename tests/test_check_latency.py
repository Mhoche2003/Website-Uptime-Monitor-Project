# The site is always reachable, only speed changes (fast, too slow, exactly at the threshold). 
# The clock of the Lambda is faked so no test really waits 40 seconds 
# We check the row saved in DynamoDB and the alert sent or not by SNS.
# Like check_availability, everything runs on a fake AWS therefore nothing real is touched.

import json
from unittest.mock import patch
from moto import mock_aws
from fake_aws import prepare_fake_aws, load_lambda

@mock_aws
def test_site_fast():
    table, sqs, queue_url, s3 = prepare_fake_aws()
    lambda_function = load_lambda("check_latency")

    # The fake clock says 1 second passed (threshold is 30)
    with patch("urllib.request.urlopen"), patch.object(lambda_function, "time") as fake_time:
        fake_time.monotonic.side_effect = [0, 1]
        result = lambda_function.lambda_handler({}, None)

    assert result["success"] is True

    rows = table.scan()["Items"]
    assert len(rows) == 1
    assert rows[0]["success"] is True

    assert "Messages" not in sqs.receive_message(QueueUrl=queue_url)


@mock_aws
def test_site_too_slow():
    table, sqs, queue_url, s3 = prepare_fake_aws()
    lambda_function = load_lambda("check_latency")

    # The fake clock says 40 seconds passed, above the threshold
    with patch("urllib.request.urlopen"), patch.object(lambda_function, "time") as fake_time:
        fake_time.monotonic.side_effect = [0, 40]
        result = lambda_function.lambda_handler({}, None)

    assert result["success"] is False

    rows = table.scan()["Items"]
    assert len(rows) == 1
    assert rows[0]["success"] is False
    assert "exceeds threshold" in rows[0]["error_message"]

    messages = sqs.receive_message(QueueUrl=queue_url)["Messages"]
    assert len(messages) == 1
    alert_text = json.loads(messages[0]["Body"])["Message"]
    assert "exceeds threshold" in alert_text


@mock_aws
def test_site_exactly_at_threshold():
    table, sqs, queue_url, s3 = prepare_fake_aws()
    lambda_function = load_lambda("check_latency")

    # Exactly 30 seconds: the code uses ">" instead of ">=", which means is still a success
    with patch("urllib.request.urlopen"), patch.object(lambda_function, "time") as fake_time:
        fake_time.monotonic.side_effect = [0, 30]
        result = lambda_function.lambda_handler({}, None)

    assert result["success"] is True

    assert "Messages" not in sqs.receive_message(QueueUrl=queue_url)
