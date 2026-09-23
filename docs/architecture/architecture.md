# Architecture

![Architecture](architecture.png)

The diagram shows the two pipelines that make up the system.

## Monitoring pipeline

An EventBridge rule triggers the 3 check Lambdas (availability, latency, content) every 5 minutes. Each one sends an HTTPS request to the monitored site, saves the result in the `check history` DynamoDB table, and publishes an alert on the SNS topic if it fails. SNS then sends an email to the site owner.

## Dashboard pipeline

A second EventBridge rule, independent from the first one, triggers the `aggregate metrics` Lambda. It reads the history from DynamoDB, calculates the metrics for the current month and writes the result to a `metrics.json` file on the dashboard S3 bucket. The dashboard is checked separately by the site owner.

## Why two separate pipelines

The checks and the metrics aggregation don't need to run at the same frequency: the checks need to be reactive (every 5 minutes) to catch an outage fast, while the dashboard doesn't need to be updated as often. Splitting the two avoids recalculating the metrics on every single check.
