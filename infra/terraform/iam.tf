# Trust an existing GitHub Actions OIDC provider; never use static AWS keys.
data "aws_iam_policy_document" "github_assume_role" {
  statement {
    sid     = "GitHubOidcExactRepositoryAndBranch"
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [var.github_oidc_provider_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:ref:refs/heads/${var.github_deploy_branch}"]
    }
  }
}

resource "aws_iam_role" "artifact_writer" {
  name                 = "${var.environment}-retail-artifact-writer"
  assume_role_policy   = data.aws_iam_policy_document.github_assume_role.json
  max_session_duration = 3600
  tags                 = local.tags
}

data "aws_iam_policy_document" "artifact_writer" {
  statement {
    sid       = "ListOnlyArtifactPrefix"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.artifacts.arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["${var.artifact_prefix}/*"]
    }
  }
  statement {
    sid       = "ReadWriteOnlyArtifactPrefix"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.artifacts.arn}/${var.artifact_prefix}/*"]
  }
}

resource "aws_iam_role_policy" "artifact_writer" {
  name   = "artifact-prefix-access"
  role   = aws_iam_role.artifact_writer.id
  policy = data.aws_iam_policy_document.artifact_writer.json
}
