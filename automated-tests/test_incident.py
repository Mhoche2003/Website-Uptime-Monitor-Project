# Tests of incident.py, the file shared by the 3 check Lambdas.
# One test per rule of the decision table: open, stay silent, stay open, close.
# Each test calls handle_result like a Lambda does, then checks the incident board and the emails.
# Everything runs on a fake AWS therefore nothing real is touched.

import json
import os

import boto3
from moto import mock_aws

from fake_aws import prepare_fake_aws
import incident


# Prepares the fake AWS and the tools a Lambda would get
def start():
    # Same fake AWS as the other tests, plus an sns client like the Lambdas have
    table, sqs, queue_url, s3 = prepare_fake_aws()
    sns = boto3.client("sns")
    topic_arn = os.environ["SNS_TOPIC_ARN"]
    return table, sns, topic_arn, sqs, queue_url


# Simulates a Lambda whose check failed
def fail(box, check, message="Request failed", unreachable=False):
    table, sns, topic_arn = box
    incident.handle_result(table, sns, topic_arn, check, False, message, unreachable)


# Simulates a Lambda whose check succeeded
def ok(box, check):
    table, sns, topic_arn = box
    incident.handle_result(table, sns, topic_arn, check, True)


def emails(sqs, queue_url):
    # Returns the emails sent since the last call, then deletes them
    texts = []
    while True:
        messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10).get("Messages", [])
        if not messages:
            return texts
        for message in messages:
            texts.append(json.loads(message["Body"])["Message"])
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])


# Reads the incident board from the table
def board(table):
    return table.get_item(Key=incident.BOARD_KEY)["Item"]


@mock_aws
def test_first_failure_opens_the_incident():
    table, sns, topic_arn, sqs, queue_url = start()
    box = (table, sns, topic_arn)

    fail(box, "content", "Expected content 'X' not found on page")

    sent = emails(sqs, queue_url)
    assert len(sent) == 1
    assert "Detected by: content check" in sent[0]
    assert "not found on page" in sent[0]

    current = board(table)
    assert current["status"] == "open"
    assert current["fail_content"] is True
    assert current["fail_availability"] is False
    assert current["fail_latency"] is False


@mock_aws
def test_same_check_failing_again_is_silent():
    table, sns, topic_arn, sqs, queue_url = start()
    box = (table, sns, topic_arn)

    fail(box, "content")
    emails(sqs, queue_url)
    fail(box, "content")

    assert emails(sqs, queue_url) == []


@mock_aws
def test_another_check_failing_is_silent_but_noted():
    table, sns, topic_arn, sqs, queue_url = start()
    box = (table, sns, topic_arn)

    fail(box, "content")
    emails(sqs, queue_url)
    fail(box, "latency", "Response time too long")

    # No new email, but the board knows that latency fails too
    assert emails(sqs, queue_url) == []
    current = board(table)
    assert current["fail_content"] is True
    assert current["fail_latency"] is True
    assert current["status"] == "open"


@mock_aws
def test_success_keeps_the_incident_open_while_another_check_fails():
    table, sns, topic_arn, sqs, queue_url = start()
    box = (table, sns, topic_arn)

    # The page content is broken but the site still answers, so availability is fine.
    # It must not close the incident.
    fail(box, "content")
    emails(sqs, queue_url)
    ok(box, "availability")

    assert emails(sqs, queue_url) == []
    current = board(table)
    assert current["status"] == "open"
    assert current["fail_content"] is True


@mock_aws
def test_last_success_closes_the_incident():
    table, sns, topic_arn, sqs, queue_url = start()
    box = (table, sns, topic_arn)

    fail(box, "content", "content is missing")
    fail(box, "latency", "latency is too high")
    emails(sqs, queue_url)

    # content is back but latency still fails, so the incident stays open
    ok(box, "content")
    assert emails(sqs, queue_url) == []
    assert board(table)["status"] == "open"

    # latency is back too, now everything is fine
    ok(box, "latency")
    sent = emails(sqs, queue_url)
    assert len(sent) == 1
    assert "Incident resolved" in sent[0]
    # The email lists the checks that were affected, with their message
    assert "content: content is missing" in sent[0]
    assert "latency: latency is too high" in sent[0]

    current = board(table)
    assert current["status"] == "closed"
    assert "opened_at" not in current


@mock_aws
def test_success_without_a_board_does_nothing():
    table, sns, topic_arn, sqs, queue_url = start()
    box = (table, sns, topic_arn)

    ok(box, "availability")

    assert emails(sqs, queue_url) == []
    # No incident ever, so no board is created either
    assert "Item" not in table.get_item(Key=incident.BOARD_KEY)


@mock_aws
def test_three_failures_in_a_row_send_one_email():
    table, sns, topic_arn, sqs, queue_url = start()
    box = (table, sns, topic_arn)

    # The site is down: the 3 checks fail one after the other
    fail(box, "availability", "Request failed: site is down", unreachable=True)
    fail(box, "latency", "Request failed: site is down", unreachable=True)
    fail(box, "content", "Request failed: site is down", unreachable=True)

    assert len(emails(sqs, queue_url)) == 1
    current = board(table)
    assert current["fail_availability"] is True
    assert current["fail_latency"] is True
    assert current["fail_content"] is True


@mock_aws
def test_unreachable_site_adds_a_hint():
    table, sns, topic_arn, sqs, queue_url = start()
    box = (table, sns, topic_arn)

    fail(box, "latency", "Request failed: site is down", unreachable=True)

    sent = emails(sqs, queue_url)
    assert "other checks are probably affected" in sent[0]


@mock_aws
def test_missing_content_has_no_hint():
    table, sns, topic_arn, sqs, queue_url = start()
    box = (table, sns, topic_arn)

    # Only the content is wrong, the other checks are fine, so no hint
    fail(box, "content", "Expected content not found on page")

    sent = emails(sqs, queue_url)
    assert "other checks are probably affected" not in sent[0]


@mock_aws
def test_a_new_incident_sends_a_new_email_after_the_close():
    table, sns, topic_arn, sqs, queue_url = start()
    box = (table, sns, topic_arn)

    fail(box, "content")
    ok(box, "content")
    emails(sqs, queue_url)

    fail(box, "availability", "Request failed")

    sent = emails(sqs, queue_url)
    assert len(sent) == 1
    assert "Detected by: availability check" in sent[0]
    current = board(table)
    assert current["status"] == "open"
    # The first incident is over, content is not part of this one
    assert current["fail_content"] is False
