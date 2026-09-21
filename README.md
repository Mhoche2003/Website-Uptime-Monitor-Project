# Website Uptime Monitor

Website Uptime monitor is a serverless monitoring system for a website build with AWS and Terraform only. It is part of my personal project on AWS during my 5th year degree as computer science student to learn more about AWS architecture and Iac notions.

## Problem

One of the most fear for a website owner it's that it break down with anyone being aware of at time which considerally impact global cost and reputation of regularly customer and the potenital new. This project realize several check for the target website at regular intervals. Then it records each result and aler the owner within second as soon as a problem has been detected.

## What it does

Three independent checks run periodically on the monitored website. The availability check verify if the site respond or if there is a network or server problem. The latency check verify how fast the site load since visitors tend to leave when it take too long. The content check verify if the page show the expected content without any error message. If one of the check fail an SNS notification is sent immediately by email with the reason of the failure. Each result is stored in DynamoDB with the timestamp and the response time and the success or failure status and the error message if any so it build an history over time. A static dashboard hosted on S3 display the key metrics like the uptime percentage and the average response time and the recent incidents.

## Architecture

The diagram below represent the whole system from the check scheduling to the three Lambda functions the history storage the alert system and the dashboard feed.

![Architecture](docs/architecture/architecture.png)

## Stack

The project use AWS services like Lambda DynamoDB SNS S3 and EventBridge to run everything without any server to manage. Terraform handle the infrastructure as code and keep a remote state on S3 with a lock table on DynamoDB. The Lambda functions are written in Python. Everything is versioned on GitHub and the architecture diagram was made with LucidChart.

## Status

The project is build incrementally one validated piece at a time. Check the commit history to see the detail of the progress. Phase 1 which cover the infrastructure foundations like the Terraform backend the history table the alert system and the architecture diagram is done. Phase 2 which is the three Lambda checks logic is in progress.

## Author

Maxime Hochereau final year computer science engineering student currently doing my end of studies internship at Devoteam A Cloud. Career goal is cloud architect then cloud cybersecurity.
