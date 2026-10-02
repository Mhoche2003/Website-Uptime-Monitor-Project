# The site answers and the Lambda checks that the page really shows what is expected ("Website Uptime Monitor"). 
# Three cases: the right page, an error page that does not contain the text, and a site that is down.
# For each one, we check the row saved in DynamoDB and the alert sent or not.
# Same goes for both check_availability and check_latency

import json
import urllib.error
from unittest.mock import patch

from moto import mock_aws

from fake_aws import prepare_fake_aws, load_lambda


@mock_aws
def test_expected_text_present():
    table, sqs, queue_url, s3 = prepare_fake_aws()
    lambda_function = load_lambda("check_content")

    # Fake page with the expected text iis set in fake_aws.py)
    page = b"<html><h1>Website Uptime Monitor</h1></html>"
    with patch("urllib.request.urlopen") as fake_urlopen:
        fake_urlopen.return_value.__enter__.return_value.read.return_value = page
        result = lambda_function.lambda_handler({}, None)

    assert result["success"] is True

    rows = table.scan()["Items"]
    assert len(rows) == 1
    assert rows[0]["success"] is True

    assert "Messages" not in sqs.receive_message(QueueUrl=queue_url)


@mock_aws
def test_expected_text_missing():
    table, sqs, queue_url, s3 = prepare_fake_aws()
    lambda_function = load_lambda("check_content")

    # The site answers but the page is an error message though which means its only a availibily 
    # check would say "OK" here only this check catches it.
    page = b"<html><h1>500 Internal Server Error</h1></html>"
    with patch("urllib.request.urlopen") as fake_urlopen:
        fake_urlopen.return_value.__enter__.return_value.read.return_value = page
        result = lambda_function.lambda_handler({}, None)

    assert result["success"] is False

    rows = table.scan()["Items"]
    assert len(rows) == 1
    assert rows[0]["success"] is False
    assert "not found on page" in rows[0]["error_message"]

    messages = sqs.receive_message(QueueUrl=queue_url)["Messages"]
    assert len(messages) == 1
    alert_text = json.loads(messages[0]["Body"])["Message"]
    assert "not found on page" in alert_text


@mock_aws
def test_site_unreachable():
    table, sqs, queue_url, s3 = prepare_fake_aws()
    lambda_function = load_lambda("check_content")

    # The site is down: urlopen fails before any page is read
    no_network = urllib.error.URLError("no network")
    with patch("urllib.request.urlopen", side_effect=no_network):
        result = lambda_function.lambda_handler({}, None)

    assert result["success"] is False

    rows = table.scan()["Items"]
    assert rows[0]["success"] is False
    assert "Request failed" in rows[0]["error_message"]

    messages = sqs.receive_message(QueueUrl=queue_url)["Messages"]
    assert len(messages) == 1
