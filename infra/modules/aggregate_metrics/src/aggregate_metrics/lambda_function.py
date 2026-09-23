import json
import os
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

# From terraform
TABLE_NAME = os.environ["DYNAMODB_TABLE"]
BUCKET_NAME = os.environ["DASHBOARD_BUCKET"]

# AWS clients are created here, outside the function, so they are not recreated on every call
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
s3 = boto3.client("s3")

CHECK_TYPES = ["availability", "latency", "content"]


def lambda_handler(event, context):
    now = datetime.now(timezone.utc)
    # The current month always starts on the 1st at midnight
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # We fetch the rows of the current month separately for each check type
    items_by_check = {
        check_type: get_month_items(check_type, period_start, now)
        for check_type in CHECK_TYPES
    }

    availability_items = items_by_check["availability"]
    latency_items = items_by_check["latency"]

    # Availability is calculated only from the availability check
    total_availability = len(availability_items)
    success_availability = sum(1 for item in availability_items if item["success"])
    availability_percent = round((success_availability / total_availability) * 100, 2) if total_availability else 0

    # The average response time is calculated only from the latency check
    response_times = [float(item["response_time"]) for item in latency_items]
    average_response_time = round(sum(response_times) / len(response_times), 3) if response_times else 0

    # We count the failures and the total checks for each type, without grouping them into incidents
    failures_by_check = {}
    total_checks_by_check = {}
    for check_type, items in items_by_check.items():
        total_checks_by_check[check_type] = len(items)
        failures_by_check[check_type] = sum(1 for item in items if not item["success"])

    metrics = {
        "generated_at": now.isoformat(),
        "period": {
            "start": period_start.isoformat(),
            "end": now.isoformat(),
        },
        "availability_percent": availability_percent,
        "average_response_time_seconds": average_response_time,
        "failures_by_check": failures_by_check,
        "total_checks_by_check": total_checks_by_check,
    }

    # We write the result as JSON directly to the dashboard bucket, the file overwrites the previous one on every run
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key="metrics.json",
        Body=json.dumps(metrics),
        ContentType="application/json",
    )

    return metrics


def get_month_items(check_type, period_start, now):
    # The table is queried with Query instead of Scan since we know the partition key (check_type), it's faster and cheaper
    items = []
    query_kwargs = {
        "KeyConditionExpression": Key("check_type").eq(check_type)
        & Key("timestamp").between(period_start.isoformat(), now.isoformat())
    }

    while True:
        response = table.query(**query_kwargs)
        items.extend(response["Items"])

        # DynamoDB limits a response to 1MB, LastEvaluatedKey shows if there is still data left to fetch
        if "LastEvaluatedKey" not in response:
            break
        query_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    return items
