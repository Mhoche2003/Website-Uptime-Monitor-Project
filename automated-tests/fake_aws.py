# Shared setup for all the tests

import os
import importlib.util
from pathlib import Path

import boto3

# boto3 needs a region
os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULES = REPO_ROOT / "infra" / "modules"

# The 4 Lambdas have the same file name, load them by path
LAMBDA_FILES = {
    "check_availability": MODULES / "lambda_checks/src/check_availability/lambda_function.py",
    "check_latency": MODULES / "lambda_checks/src/check_latency/lambda_function.py",
    "check_content": MODULES / "lambda_checks/src/check_content/lambda_function.py",
    "aggregate_metrics": MODULES / "aggregate_metrics/src/aggregate_metrics/lambda_function.py",
}


def prepare_fake_aws():
    """Fake AWS for one test. Call it inside a @mock_aws test."""

    # Same keys as the real table
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.create_table(
        TableName="test-table",
        KeySchema=[
            {"AttributeName": "check_type", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "check_type", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # SNS doesn't keep its messages, so a queue receives the alerts for us
    sns = boto3.client("sns")
    sqs = boto3.client("sqs")
    topic_arn = sns.create_topic(Name="test-topic")["TopicArn"]
    queue_url = sqs.create_queue(QueueName="test-queue")["QueueUrl"]
    queue_arn = sqs.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["QueueArn"]
    )["Attributes"]["QueueArn"]
    sns.subscribe(TopicArn=topic_arn, Protocol="sqs", Endpoint=queue_arn)

    # Only used by aggregate_metrics
    s3 = boto3.client("s3")
    s3.create_bucket(
        Bucket="test-bucket",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
    )

    # Settings that Terraform gives to the real Lambdas
    os.environ["SITE_URL"] = "https://example.test"
    os.environ["DYNAMODB_TABLE"] = "test-table"
    os.environ["SNS_TOPIC_ARN"] = topic_arn
    os.environ["DASHBOARD_BUCKET"] = "test-bucket"
    os.environ["LATENCY_THRESHOLD"] = "30"
    os.environ["EXPECTED_CONTENT"] = "Website Uptime Monitor"

    return table, sqs, queue_url, s3


def load_lambda(name):
    """Load a Lambda by its short name."""
    spec = importlib.util.spec_from_file_location(name, LAMBDA_FILES[name])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
