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
LATENCY_THRESHOLD = float(os.environ["LATENCY_THRESHOLD"])

# AWS clients are created here, outside the function, so they are not recreated on every call
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)
sns = boto3.client("sns")


def lambda_handler(event, context):
    timestamp = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    success = True
    error_message = ""

    # We measure the response time
    try:
        with urllib.request.urlopen(SITE_URL, timeout=LATENCY_THRESHOLD + 5): #the timeout is larger than the threshold so we can actually measure it
            pass
    except urllib.error.URLError as e:
        success = False
        error_message = f"Request failed: {e}"

    response_time = time.monotonic() - start

    if success and response_time > LATENCY_THRESHOLD:
        success = False
        error_message = f"Response time {response_time:.2f}s exceeds threshold of {LATENCY_THRESHOLD}s"

    # We save the check result in DynamoDB on every run (success or failure)
    table.put_item(Item={
        "check_type": "latency",
        "timestamp": timestamp,
        "success": success,
        "response_time": Decimal(str(response_time)),
        "error_message": error_message,
    })

    # Alert sent only if the response time is above the threshold
    if not success:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Website Uptime Monitor - latency check failed",
            Message=f"Latency check failed at {timestamp}.\nReason: {error_message}",
        )

    return {"success": success, "response_time": response_time}
