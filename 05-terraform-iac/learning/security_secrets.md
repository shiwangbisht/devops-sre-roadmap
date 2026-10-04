# Terraform — security & secrets

Secrets are the single most common way Terraform shows up in a security incident — not because the tool
is unsafe, but because it's easy to treat `.tf` files like regular app config instead of something that
can leak credentials into git history, logs, and a plaintext state file. This is the part that gets
asked about disproportionately in SRE interviews relative to how often it comes up in tutorials.

## Never hardcode secrets in config

```hcl
# WRONG — ends up in git history, every clone, and CI logs
resource "aws_db_instance" "main" {
  password = "SuperSecret123"
}
```

```hcl
# RIGHT — reference a secret manager, never the literal value
data "aws_secretsmanager_secret_version" "db" {
  secret_id = "prod/db/password"
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db.secret_string
}
```
Same principle applies with SSM Parameter Store (`aws_ssm_parameter` data source with `with_decryption
= true`) or HashiCorp Vault (`vault` provider). A private repo is **not** an equivalent control — it
still leaves the secret in git history, in everyone-with-access's working copy, and often in CI logs.

## State itself is a secrets risk, independent of your config

Even with zero hardcoded secrets, state stores **every attribute a provider returns**, including
generated values — an RDS password passed as an argument, a generated API key, a TLS private key
resource's `private_key_pem`. Marking a variable `sensitive = true` only redacts CLI output — it does
**not** encrypt the value in state.

Mitigations:
- Encrypt the state backend at rest (S3 SSE, Terraform Cloud's built-in encryption).
- Access-control the state backend like you would a credentials store, not like a regular artifact bucket.
- Avoid resources that *necessarily* put long-lived secrets in state when an alternative exists (e.g.
  let RDS generate+manage a password via `manage_master_user_password = true` instead of passing one in).

## Least-privilege IAM for Terraform's own execution identity

The role/user Terraform runs as (locally or in CI) needs exactly the permissions required to manage the
resources in that config — not org-wide admin. Separate roles per environment (`dev`-apply vs
`prod`-apply) so a mistake or compromise in one pipeline can't reach another environment's infra.

```hcl
# Example shape, not literal policy: scope the CI role to only what this config manages
resource "aws_iam_role_policy" "terraform_ci" {
  role = aws_iam_role.terraform_ci.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ec2:*", "s3:GetObject", "s3:PutObject"]
      Resource = "*"   # in reality, scope this to specific ARNs, not a wildcard
    }]
  })
}
```

## Static scanning for security misconfigurations

```bash
tfsec .        # fast, config-only scan (public buckets, open security groups, unencrypted volumes)
checkov -d .   # broader rule sets (CIS benchmarks, compliance frameworks), config + plan scanning
```
Run these as an early, fast CI gate — before the (slower, provider-API-calling) `plan` step, same logic
as running `fmt -check`/`validate` first.

## Common real misconfigurations an SRE should instinctively flag in review

- A security group with `0.0.0.0/0` ingress on anything other than a deliberately public port (443/80).
- An S3 bucket without `block_public_access` settings explicitly enabled.
- A resource storing a secret value directly as a plain `variable` default (defaults are *not*
  sensitive by definition — `sensitive = true` has to be set explicitly, and a literal default still
  lands in version control).
- Overly broad IAM policies (`"Action": "*"`, `"Resource": "*"`) applied "to get it working," never
  tightened afterward.

---

## Interview questions (with the short answer you should be able to give cold)

1. *Why is hardcoding a secret in a `.tf` file a problem even in a private repo?* — It still lands in
   git history (hard to fully purge even after removal), in every clone/working copy, and often in CI
   logs — a private repo controls *who can see the repo*, not the much narrower access a real secret
   manager gives you (audited, revocable, rotated).
2. *Does marking a variable `sensitive = true` encrypt it in state?* — No — it only redacts the value
   from CLI output (`plan`/`apply`/`output`); the value is still stored in plaintext in the state file
   unless the backend itself encrypts at rest.
3. *How do you pull a secret into Terraform config without ever writing its value in the repo?* — A
   data source against a secret manager at apply time — `aws_secretsmanager_secret_version`,
   `aws_ssm_parameter` (with decryption), or the `vault` provider — so the literal value never exists in
   version control at all.
4. *Why would you scope separate IAM roles for Terraform's dev vs. prod CI pipelines instead of one
   shared role?* — Least privilege and blast radius containment — a bug or compromise in the dev
   pipeline shouldn't be able to reach prod resources, and separate roles make audit logs clearly
   attributable per environment.
5. *What's the difference between what tfsec/checkov catch and what a human PR reviewer catches?* —
   Static scanners consistently catch known-bad patterns (public buckets, open security groups,
   missing encryption) across every PR without relying on a human remembering to check; they don't
   catch business-logic/architectural issues a human review still needs to.
6. *Given a security group open to `0.0.0.0/0` on port 22, what's wrong and how would you fix it in
   Terraform?* — SSH exposed to the entire internet — fix by scoping `cidr_blocks` to a known range
   (VPN/bastion CIDR) or removing direct SSH access in favor of SSM Session Manager, which needs no
   open inbound port at all.
7. *If a secret was accidentally committed to a public repo and later removed, is the risk over?* — No
   — it's still in git history (reachable via `git log`/old commits) and must be treated as
   compromised: rotate the actual credential, don't just delete the line from the latest commit.
8. *Why should the Terraform state backend be access-controlled as strictly as a secrets manager?* —
   Because state routinely contains secrets in plaintext (generated passwords, keys, any sensitive
   provider-returned attribute) regardless of what's marked `sensitive` in config — read access to
   state can be equivalent to read access to real credentials.