# Website Uptime Monitor

Serverless monitoring system for a website, built on AWS with Terraform. Personal project built during my final-year internship search, as a hands-on way to practice cloud architecture and infrastructure as code.

## Problem

A website going down without anyone noticing costs traffic, revenue, and trust. This project checks a target site on a schedule, logs every result, and alerts the owner within seconds when something breaks.

## What it does

Three independent checks run periodically against the monitored site:

- **Availability** — does the site respond at all (network/DNS/server errors)?
- **Latency** — how long does it take to load? Past a threshold, visitors leave.
- **Content** — does the page return the expected content, with no error page?

If any check fails, an SNS notification (email) is sent immediately with the reason. Every check result — timestamp, response time, success/failure, error message if any — is stored in DynamoDB, building a historical record. A static dashboard (hosted on S3) surfaces the key metrics: uptime percentage, average response time, and recent incidents.

## Architecture

```
CloudWatch (schedule)
      |
      v
  Lambda (3 checks) --> DynamoDB (history)
      |
      v
  SNS (alert on failure) --> Email
```

Dashboard: static site on S3, reading aggregated metrics.

## Stack

- **AWS**: Lambda, DynamoDB, SNS, S3, CloudWatch
- **Terraform**: infrastructure as code, remote state (S3 + DynamoDB lock)
- **Python**: Lambda functions
- **GitHub Actions**: planned, added once the infra is stable

## Status

Work in progress — built incrementally, one piece at a time. See commit history for progress.

## Author

Maxime Hochereau — Cloud engineering student, aiming for Cloud/Cyber Cloud Architect.
