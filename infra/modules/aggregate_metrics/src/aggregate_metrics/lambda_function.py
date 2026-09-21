import json
import os
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

# Depuis terraform
TABLE_NAME = os.environ["DYNAMODB_TABLE"]
BUCKET_NAME = os.environ["DASHBOARD_BUCKET"]

# Les clients AWS sont crees ici donc en dehors de la fonction afin de ne pas les refaire a chaque appel
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
s3 = boto3.client("s3")

CHECK_TYPES = ["availability", "latency", "content"]


def lambda_handler(event, context):
    now = datetime.now(timezone.utc)
    # Le mois en cours commence toujours le 1er a minuit
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # On recupere les lignes du mois en cours separement pour chaque type de check
    items_by_check = {
        check_type: get_month_items(check_type, period_start, now)
        for check_type in CHECK_TYPES
    }

    availability_items = items_by_check["availability"]
    latency_items = items_by_check["latency"]

    # La disponibilite est calculee uniquement sur le check availability
    total_availability = len(availability_items)
    success_availability = sum(1 for item in availability_items if item["success"])
    availability_percent = round((success_availability / total_availability) * 100, 2) if total_availability else 0

    # Le temps de reponse moyen est calcule uniquement sur le check latency
    response_times = [float(item["response_time"]) for item in latency_items]
    average_response_time = round(sum(response_times) / len(response_times), 3) if response_times else 0

    # On compte les echecs et le total de checks pour chaque type, sans les regrouper en incidents
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

    # On ecrit le resultat en JSON directement sur le bucket du dashboard, le fichier ecrase le precedent a chaque execution
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key="metrics.json",
        Body=json.dumps(metrics),
        ContentType="application/json",
    )

    return metrics


def get_month_items(check_type, period_start, now):
    # La table est interrogee avec Query plutot que Scan car on connait la partition key (check_type), c'est plus rapide et moins cher
    items = []
    query_kwargs = {
        "KeyConditionExpression": Key("check_type").eq(check_type)
        & Key("timestamp").between(period_start.isoformat(), now.isoformat())
    }

    while True:
        response = table.query(**query_kwargs)
        items.extend(response["Items"])

        # DynamoDB limite une reponse a 1MB, LastEvaluatedKey indique s'il reste des donnees a recuperer
        if "LastEvaluatedKey" not in response:
            break
        query_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    return items
