# Testing the IAM least-privilege policy - Website Uptime Monitor

The goal here is to check that the new `iam_deployer` policy is actually enough on its own to run Terraform on this project, without falling back on the broad `AdministratorAccess` policy.

## Test: detaching AdministratorAccess and running terraform plan

The new policy was applied first while `AdministratorAccess` was still attached to the deployer user, so there was no risk of getting locked out. The real test came after that: detaching `AdministratorAccess` manually and running `terraform plan` again with only the new policy active.

```
aws iam detach-user-policy --user-name Maxime --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
terraform plan
```

The first attempt failed with several `AccessDenied` errors. None of them were actions the code actually creates or changes, they were read-only actions the Terraform AWS provider calls in the background while refreshing state (`iam:ListAttachedRolePolicies`, `dynamodb:DescribeContinuousBackups`, `dynamodb:DescribeTimeToLive`, `s3:GetBucketAcl`, `s3:GetBucketCORS`, `s3:GetAccelerateConfiguration`, `s3:GetBucketRequestPayment`, `s3:GetBucketLogging`, `sns:GetSubscriptionAttributes`, and more). These calls read config details like bucket ACLs or table backup settings that aren't visible just by reading the Terraform `resource` blocks in this project's code.

Each missing action was added one at a time, straight from the exact name in the error message. Since applying a fix to the policy itself needs some access too, the cycle each time was the same: reattach `AdministratorAccess` temporarily, run `terraform apply`, detach `AdministratorAccess` again, then `terraform plan` to retest.

After a few rounds like this on S3 and DynamoDB, listing every read action by hand stopped being worth it. The read side of these two services now uses a wildcard, `s3:Get*` and `dynamodb:Describe*`, still scoped to this project's resources through the `Resource` field. Actions that create, change or delete something, like `Create`, `Put`, `Delete` and `Update`, stay listed one by one. Only reading was widened.

With that change, `terraform plan` finally came back clean:

```
No changes. Your infrastructure matches the configuration.
```

`AdministratorAccess` was then removed for good, confirmed with:

```
aws iam list-attached-user-policies --user-name Maxime
```

Only `website-uptime-monitor-deployer-policy` and the pre-existing `Billing` policy remain attached.

## Finding

Writing an IAM policy by reading the Terraform code is not enough to get it right on the first try, since the AWS provider reads far more than what is declared in the config. Plenty of read-only calls happen behind the scenes to check the current state of a resource, and there's no way to know all of them in advance. In the end, detaching the broad access and letting real `AccessDenied` errors show up was the only reliable way to find them.

This really got me interested in AWS IAM Access Analyzer, which can generate a policy directly from real CloudTrail activity. It would likely have caught all of this in one pass instead of several rounds of trial and error.
