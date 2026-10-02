# Testing the IAM least-privilege policy - Website Uptime Monitor

This test checks if the new iam_deployer policy is enough on its own to run Terraform without AdministratorAccess policy, applied by default at the beginning of the project.

## Test: detach AdministratorAccess and run terraform plan

The new policy was applied first while AdministratorAccess was still attached so it allow there was no risk of a potential lockout. The real test was detaching AdministratorAccess (`aws iam detach-user-policy`) and running terraform plan again with only the new policy active.

The first try failed with several AccessDenied errors, like iam:ListAttachedRolePolicies or s3:GetBucketAcl. None of these actions change anything since they are all read-only calls. The Terraform AWS provider makes these calls in the background to check the current state of a resource and they are not visible just by reading the code.

Each missing action was added one at a time, based on the error message. Also, to fix the policy it requires some access so the cycle was: reattach AdministratorAccess then apply the fix, detach it again and finally test with terraform plan.

After a few try on S3 and DynamoDB, listing every read action by hand became too slow. This also meant changing how the policy is written in the Terraform code: the read side of these two services now uses a wildcard instead, s3:Get* and dynamodb:Describe*, still scoped to this project's resources. However actions that create, change or delete something stay listed one by one. Basically only reading was widened.

With this change, terraform plan came back clean which means no changes. AdministratorAccess was then removed for good, confirmed with `aws iam list-attached-user-policies`: only the new policy and the pre-existing Billing policy remain attached to the user.

## Finding

The most important thing in this part was that reading the Terraform code is not enough to write a correct IAM policy on the first try. The AWS provider makes many read-only calls that are not declared anywhere in the code just to check the current state of things. Detaching the broad access and fixing the real AccessDenied errors one by one was the only reliable way to find them all.

Above all what I learnt is AWS IAM Access Analyzer can generate a policy from real usage logs instead so It would probably have found all of this in one pass instead of several rounds of trial and error.
