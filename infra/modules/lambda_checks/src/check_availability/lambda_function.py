#The 3 functions are almost identical, each one just adds one extra check.

import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from decimal import Decimal

import boto3
import incident

# From terraform
SITE_URL = os.environ["SITE_URL"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

# AWS clients are created here, outside the function, so they are not recreated on every call
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)
sns = boto3.client("sns")


def lambda_handler(event, context):
    timestamp = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    site_unreachable = False
    success = True
    error_message = ""

    try:
        with urllib.request.urlopen(SITE_URL, timeout=30) as response:
            status = response.status
            if status >= 400:
                success = False
                error_message = f"Unexpected status code: {status}"
    except urllib.error.URLError as e:
        # An HTTP error (404, 500) is also a URLError, but there the site did answer
        site_unreachable = not isinstance(e, urllib.error.HTTPError)
        success = False
        error_message = f"Request failed: {e}"

    response_time = time.monotonic() - start

    # We save the check result in DynamoDB on every run (success or failure)
    table.put_item(Item={
        "check_type": "availability",
        "timestamp": timestamp,
        "success": success,
        "response_time": Decimal(str(response_time)),
        "error_message": error_message,
    })

    # Called on every result, success too, because a success is what closes the incident
    incident.handle_result(table, sns, SNS_TOPIC_ARN, "availability", success, error_message, site_unreachable)

    return {"success": success, "response_time": response_time}
