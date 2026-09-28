data "aws_caller_identity" "current" {}

data "aws_iam_user" "deployer" {
  user_name = var.deployer_iam_user_name
}

#This policy replaces AdministratorAccess for the Terraform deployer user.
#Each action only works on resources whose name starts with the project prefix.
resource "aws_iam_policy" "deployer" {
  name        = "${var.project_name}-deployer-policy"
  description = "Least-privilege policy for the IAM user running Terraform on this project."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        #S3: create and manage our buckets. Only read and write our own objects.
        Sid    = "S3Project"
        Effect = "Allow"
        Action = [
          "s3:CreateBucket",
          "s3:DeleteBucket",
          "s3:PutBucketVersioning",
          "s3:PutBucketPolicy",
          "s3:DeleteBucketPolicy",
          "s3:PutBucketPublicAccessBlock",
          "s3:PutEncryptionConfiguration",
          "s3:PutBucketWebsite",
          "s3:DeleteBucketWebsite",
          "s3:PutBucketTagging",
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          #s3:Get* covers all the read-only checks Terraform needs (ACL, CORS, lifecycle, logging and more).
          #This saves listing every single one by hand. Resource below still limits it to our buckets.
          "s3:Get*"
        ]
        Resource = [
          "arn:aws:s3:::${var.project_name}-*",
          "arn:aws:s3:::${var.project_name}-*/*"
        ]
      },
      {
        #DynamoDB: manage our table and read/write items.
        Sid    = "DynamoDBProject"
        Effect = "Allow"
        Action = [
          "dynamodb:CreateTable",
          "dynamodb:DeleteTable",
          "dynamodb:UpdateTable",
          "dynamodb:TagResource",
          "dynamodb:UntagResource",
          "dynamodb:ListTagsOfResource",
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          #dynamodb:Describe* covers DescribeTable, DescribeContinuousBackups, DescribeTimeToLive and more.
          #Same idea as s3:Get* above.
          "dynamodb:Describe*"
        ]
        Resource = "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${var.project_name}-*"
      },
      {
        #Lambda: deploy and update our 4 functions. AddPermission lets EventBridge trigger them.
        Sid    = "LambdaProject"
        Effect = "Allow"
        Action = [
          "lambda:CreateFunction",
          "lambda:DeleteFunction",
          "lambda:GetFunction",
          "lambda:GetFunctionConfiguration",
          "lambda:UpdateFunctionCode",
          "lambda:UpdateFunctionConfiguration",
          "lambda:ListVersionsByFunction",
          "lambda:TagResource",
          "lambda:UntagResource",
          "lambda:ListTags",
          "lambda:AddPermission",
          "lambda:RemovePermission",
          "lambda:GetPolicy",
          # The AWS provider reads this during refresh for every Lambda function,
          # even though this project doesn't use code signing.
          "lambda:GetFunctionCodeSigningConfig"
        ]
        Resource = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-*"
      },
      {
        #EventBridge: manage the schedules that trigger our Lambdas.
        Sid    = "EventBridgeProject"
        Effect = "Allow"
        Action = [
          "events:PutRule",
          "events:DeleteRule",
          "events:DescribeRule",
          "events:PutTargets",
          "events:RemoveTargets",
          "events:ListTargetsByRule",
          "events:TagResource",
          "events:UntagResource",
          "events:ListTagsForResource"
        ]
        Resource = "arn:aws:events:${var.aws_region}:${data.aws_caller_identity.current.account_id}:rule/${var.project_name}-*"
      },
      {
        #SNS: manage the alert topic and the email subscription.
        Sid    = "SNSProject"
        Effect = "Allow"
        Action = [
          "sns:CreateTopic",
          "sns:DeleteTopic",
          "sns:GetTopicAttributes",
          "sns:SetTopicAttributes",
          "sns:Subscribe",
          "sns:Unsubscribe",
          "sns:ListSubscriptionsByTopic",
          "sns:GetSubscriptionAttributes",
          "sns:TagResource",
          "sns:UntagResource",
          "sns:ListTagsForResource"
        ]
        Resource = "arn:aws:sns:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.project_name}-*"
      },
      {
        Sid    = "LogsProject"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:DeleteLogGroup",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:PutRetentionPolicy",
          "logs:TagResource",
          "logs:ListTagsForResource"
        ]
        #Lambda creates one log group per function automatically. The group name matches the function name.
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-*"
      },
      {
        #Read-only browsing across the whole account, not just this project's resources.
        #These List/Describe/Get actions don't support resource-level restriction in AWS (they only work with Resource "*"),
        #so this statement stays separate from the scoped ones above: it only adds visibility, never the ability
        #to create, modify or delete anything beyond what the other statements already allow.
        #events:ListRuleNamesByTarget specifically is what the Lambda console needs to show the EventBridge
        #trigger box on a function's page (it looks up which rules target that function).
        Sid    = "ConsoleReadOnlyBrowsing"
        Effect = "Allow"
        Action = [
          "s3:ListAllMyBuckets",
          "s3:GetBucketLocation",
          "lambda:ListFunctions",
          "lambda:GetAccountSettings",
          "dynamodb:ListTables",
          "sns:ListTopics",
          "events:ListRuleNamesByTarget",
          "logs:DescribeLogGroups",
          "cloudwatch:GetMetricData"
        ]
        Resource = "*"
      },
      {
        #IAM: manage the 2 execution roles used by our Lambdas. Nothing outside this project.
        Sid    = "IAMRolesProject"
        Effect = "Allow"
        Action = [
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:GetRole",
          "iam:PutRolePolicy",
          "iam:GetRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies",
          "iam:TagRole",
          "iam:UntagRole"
        ]
        Resource = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.project_name}-*"
      },
      {
        Sid      = "IAMPassRoleLambdaOnly"
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.project_name}-*"
        #This condition means the role can only go to the Lambda service. Never to anything else.
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "lambda.amazonaws.com"
          }
        }
      },
      {
        #These two statements let Terraform manage this same policy and its attachment to the deployer user later
        #once AdministratorAccess is removed and this policy becomes the only one left on the user.
        Sid    = "IAMSelfManagePolicy"
        Effect = "Allow"
        Action = [
          "iam:CreatePolicy",
          "iam:DeletePolicy",
          "iam:GetPolicy",
          "iam:GetPolicyVersion",
          "iam:CreatePolicyVersion",
          "iam:DeletePolicyVersion",
          "iam:ListPolicyVersions",
          "iam:TagPolicy"
        ]
        Resource = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/${var.project_name}-*"
      },
      {
        Sid    = "IAMSelfManageAttachment"
        Effect = "Allow"
        Action = [
          "iam:GetUser",
          "iam:AttachUserPolicy",
          "iam:DetachUserPolicy",
          "iam:ListAttachedUserPolicies"
        ]
        Resource = data.aws_iam_user.deployer.arn
      },
      {
        #AWS always allows this action. Listed here to keep the policy explicit.
        Sid      = "STSIdentity"
        Effect   = "Allow"
        Action   = "sts:GetCallerIdentity"
        Resource = "*"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_user_policy_attachment" "deployer" {
  user       = data.aws_iam_user.deployer.user_name
  policy_arn = aws_iam_policy.deployer.arn
}
