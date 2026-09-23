import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from decimal import Decimal

import boto3

# From terraform
SITE_URL = os.environ["SITE_URL"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
EXPECTED_CONTENT = os.environ["EXPECTED_CONTENT"]

# AWS clients are created here, outside the function, so they are not recreated on every call
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)
sns = boto3.client("sns")


def lambda_handler(event, context):
    timestamp = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    success = True
    error_message = ""

    # We check that the expected text is actually present on the page
    try:
        with urllib.request.urlopen(SITE_URL, timeout=30) as response:
            body = response.read().decode("utf-8", errors="replace")
            if EXPECTED_CONTENT not in body:
                success = False
                error_message = f"Expected content '{EXPECTED_CONTENT}' not found on page"
    except urllib.error.URLError as e:
        success = False
        error_message = f"Request failed: {e}"

    response_time = time.monotonic() - start

    # We save the check result in DynamoDB on every run (success or failure)
    table.put_item(Item={
        "check_type": "content",
        "timestamp": timestamp,
        "success": success,
        "response_time": Decimal(str(response_time)),
        "error_message": error_message,
    })

    # An alert is only sent when the expected text is missing
    if not success:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Website Uptime Monitor - content check failed",
            Message=f"Content check failed at {timestamp}.\nReason: {error_message}",
        )

    return {"success": success, "response_time": response_time}
