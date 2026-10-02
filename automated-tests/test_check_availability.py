# The site simulated (200, 404, no network) and check what the Lambda does:
# the row saved in DynamoDB and the alert sent (or not) by SNS.
# Same goes for both check_availability and latency

import json
import urllib.error
from unittest.mock import patch

from moto import mock_aws

from fake_aws import prepare_fake_aws, load_lambda


# moto = fake AWS
@mock_aws
def test_site_ok():
    table, sqs, queue_url, s3 = prepare_fake_aws()
    lambda_function = load_lambda("check_availability")

    # Fake urlopen: the site answers 200
    with patch("urllib.request.urlopen") as fake_urlopen:
        fake_urlopen.return_value.__enter__.return_value.status = 200
        result = lambda_function.lambda_handler({}, None)

    assert result["success"] is True

    # One row saved, even if everything is fine to keep the historical 
    rows = table.scan()["Items"]
    assert len(rows) == 1
    assert rows[0]["success"] is True

    assert "Messages" not in sqs.receive_message(QueueUrl=queue_url)


@mock_aws
def test_site_returns_404():
    table, sqs, queue_url, s3 = prepare_fake_aws()
    lambda_function = load_lambda("check_availability")

    # The real urlopen raises an error on a 404
    error_404 = urllib.error.HTTPError(
        "https://example.test", 404, "Not Found", None, None
    )
    with patch("urllib.request.urlopen", side_effect=error_404):
        result = lambda_function.lambda_handler({}, None)

    assert result["success"] is False

    # The failure is saved with the reason
    rows = table.scan()["Items"]
    assert len(rows) == 1
    assert rows[0]["success"] is False
    assert "404" in rows[0]["error_message"]

    # One alert, read from the queue
    messages = sqs.receive_message(QueueUrl=queue_url)["Messages"]
    assert len(messages) == 1
    alert_text = json.loads(messages[0]["Body"])["Message"]
    assert "404" in alert_text


@mock_aws
def test_site_unreachable():
    table, sqs, queue_url, s3 = prepare_fake_aws()
    lambda_function = load_lambda("check_availability")

    # No network at all
    no_network = urllib.error.URLError("no network")
    with patch("urllib.request.urlopen", side_effect=no_network):
        result = lambda_function.lambda_handler({}, None)

    assert result["success"] is False

    rows = table.scan()["Items"]
    assert rows[0]["success"] is False
    assert "Request failed" in rows[0]["error_message"]

    messages = sqs.receive_message(QueueUrl=queue_url)["Messages"]
    assert len(messages) == 1
