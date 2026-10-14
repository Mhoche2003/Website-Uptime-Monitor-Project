# Shared by the 3 check Lambdas.
# The incident board is one item in the history table: one switch per check and a status (open or closed).
# Each Lambda reports its result here, which sends at most one email.
# table and sns come from the Lambda, so nothing is created here.

from datetime import datetime, timezone

from botocore.exceptions import ClientError

CHECKS = ("availability", "latency", "content")

# board lives in the same table as the history with a fixed key
#All lambdas write on the same item thanks incident/state as a fix adress
BOARD_KEY = {"check_type": "incident", "timestamp": "state"}


# Entry point for the Lambdas. Call it once per run, after the result is saved in the history.
def handle_result(table, sns, topic_arn, check, success, error_message="", site_unreachable=False):
    if success:
        _check_ok(table, sns, topic_arn, check)
    else:
        _check_failed(table, sns, topic_arn, check, error_message, site_unreachable)


# Switches the check on. Sends the opened email only if the incident was not open yet.
def _check_failed(table, sns, topic_arn, check, error_message, site_unreachable):
    now = datetime.now(timezone.utc).isoformat()

    # One atomic update, so two Lambdas at the same time can't both open the incident.
    # Our switch goes on and the other two are created off if they are missing.
    sets = [
        "#status = :open",
        f"fail_{check} = :on",
        f"error_{check} = :message",
        "opened_at = if_not_exists(opened_at, :now)",
        "opened_by = if_not_exists(opened_by, :check)",
    ]
    for other in CHECKS:
        if other != check:
            sets.append(f"fail_{other} = if_not_exists(fail_{other}, :off)")

    # ALL_OLD returns the board as it was before this update
    response = table.update_item(
        Key=BOARD_KEY,
        UpdateExpression="SET " + ", ".join(sets),
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":open": "open",
            ":on": True,
            ":off": False,
            ":message": error_message,
            ":now": now,
            ":check": check,
        },
        ReturnValues="ALL_OLD",
    )
    old_board = response.get("Attributes", {})

    # Already open means another Lambda sent the email, so we do nothing
    if old_board.get("status") == "open":
        return

    text = f"Incident opened at {now}.\nDetected by: {check} check.\nReason: {error_message}"
    if site_unreachable:
        text += "\nThe site looks unreachable, so the other checks are probably affected too."
    sns.publish(
        TopicArn=topic_arn,
        Subject="Website Uptime Monitor - incident opened",
        Message=text,
    )


# Switches the check off. Closes the incident and sends the resolved email only if no switch is left on.
def _check_ok(table, sns, topic_arn, check):
    now = datetime.now(timezone.utc).isoformat()

    # Switch off only if the board exists. No board means no incident, so nothing to do.
    try:
        response = table.update_item(
            Key=BOARD_KEY,
            UpdateExpression=f"SET fail_{check} = :off",
            ConditionExpression="attribute_exists(check_type)",
            ExpressionAttributeValues={":off": False},
            ReturnValues="ALL_NEW",
        )
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return
        raise
    board = response["Attributes"]
                                     
    if board.get("status") != "open":  #The incident stays open while one switch is still on
        return
    if any(board.get(f"fail_{name}") for name in CHECKS):
        return

    # All switches are off. The condition makes sure only one Lambda closes the incident.
    try:
        response = table.update_item(
            Key=BOARD_KEY,
            UpdateExpression=(
                "SET #status = :closed, closed_at = :now "
                "REMOVE opened_at, opened_by, error_availability, error_latency, error_content"
            ),
            ConditionExpression=(
                "#status = :open AND fail_availability = :off "
                "AND fail_latency = :off AND fail_content = :off"
            ),
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":closed": "closed",
                ":open": "open",
                ":off": False,
                ":now": now,
            },
            ReturnValues="ALL_OLD",
        )
    except ClientError as error:
        # Condition failed: another Lambda closed it first or a check failed again in between
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return
        raise
    old_board = response["Attributes"]

    opened_at = old_board.get("opened_at", now) 
    minutes = _minutes_between(opened_at, now)
    lines = [
        f"Incident resolved at {now}.",
        f"Opened at {opened_at} ({minutes} minutes ago).",
        "Checks affected during the incident:",
    ]
    for name in CHECKS:
        if f"error_{name}" in old_board:
            lines.append(f"{name}: {old_board[f'error_{name}']}")
    sns.publish(
        TopicArn=topic_arn,
        Subject="Website Uptime Monitor - incident resolved",
        Message="\n".join(lines),
    )


# Time between two ISO dates in minutes, used in the resolved email.
def _minutes_between(start, end):
    seconds = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
    return round(seconds / 60, 1)
