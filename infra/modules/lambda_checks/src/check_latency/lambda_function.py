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
LATENCY_THRESHOLD = float(os.environ["LATENCY_THRESHOLD"])

# Les clients AWS sont crees ici donc en dehors de la fonction afin de ne pas les refaire a chaque appel
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)
sns = boto3.client("sns")


def lambda_handler(event, context):
    timestamp = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    success = True
    error_message = ""

    # On mesure le temps de reponse 
    try:
        with urllib.request.urlopen(SITE_URL, timeout=LATENCY_THRESHOLD + 5): #le timeout est plus large que le seuil pour bien le mesurer
            pass
    except urllib.error.URLError as e:
        success = False
        error_message = f"Request failed: {e}"

    response_time = time.monotonic() - start

    if success and response_time > LATENCY_THRESHOLD:
        success = False
        error_message = f"Response time {response_time:.2f}s exceeds threshold of {LATENCY_THRESHOLD}s"

    # On enregistre le resultat du check dans DynamoDB a chaque execution (succes ou echec)
    table.put_item(Item={
        "check_type": "latency",
        "timestamp": timestamp,
        "success": success,
        "response_time": Decimal(str(response_time)),
        "error_message": error_message,
    })

    # Alerte envoyee seulement si le temps de reponse > seuil
    if not success:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Website Uptime Monitor - latency check failed",
            Message=f"Latency check failed at {timestamp}.\nReason: {error_message}",
        )

    return {"success": success, "response_time": response_time}
