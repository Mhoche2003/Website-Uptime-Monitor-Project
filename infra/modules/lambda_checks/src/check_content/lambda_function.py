import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from decimal import Decimal

import boto3

# Depuis terraform
SITE_URL = os.environ["SITE_URL"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
EXPECTED_CONTENT = os.environ["EXPECTED_CONTENT"]

# Les clients AWS sont crees ici donc en dehors de la fonction afin de ne pas les refaire a chaque appel
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)
sns = boto3.client("sns")


def lambda_handler(event, context):
    timestamp = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    success = True
    error_message = ""

    # On verifie que le texte attendu est bien present sur la page
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

    # On enregistre le resultat du check dans DynamoDB a chaque execution (succes ou echec)
    table.put_item(Item={
        "check_type": "content",
        "timestamp": timestamp,
        "success": success,
        "response_time": Decimal(str(response_time)),
        "error_message": error_message,
    })

    # Une alerte est envoyee seulement quand le texte attendu est absent
    if not success:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Website Uptime Monitor - content check failed",
            Message=f"Content check failed at {timestamp}.\nReason: {error_message}",
        )

    return {"success": success, "response_time": response_time}
