# Security

NudgeBand is a public, open-source project. This page says how to report a
problem and what the automatic checks look for.

## Reporting a vulnerability

Please report security problems privately through GitHub:
**Security tab → Report a vulnerability** on this repository. Do not open a
public issue for anything that could hurt users (for example a way to pair
with or control someone else's band). You should hear back within a week.

## Automatic checks on every pull request

| Check | Workflow | What it catches |
| --- | --- | --- |
| Secret scan | `security.yml` → gitleaks | API keys, tokens, passwords and private keys in any commit on any branch (output is redacted) |
| Privacy check | `security.yml` → `.github/scripts/privacy-check.py` | Home-folder paths that show a user name, personal cloud-drive paths, email addresses, confidential or NDA markings, vendor datasheet PDFs, key and keystore files, `.env` and `local.properties`, very large files. Warns when a commit uses a personal email address |
| Workflow audit | `security.yml` → zizmor | Unsafe GitHub Actions patterns: script injection, unpinned actions, leaked tokens, too-broad permissions |
| Dependency review | `security.yml` | New dependencies with known vulnerabilities (moderate or worse) |
| Code scanning | `codeql.yml` | Security bugs in the firmware (C), Android app (Kotlin), Python scripts and workflows |
| Dependabot | `dependabot.yml` | Weekly updates for pinned Actions and Android libraries |

The same checks also run on `main` and once a week, so new rules catch old code.

If the privacy check flags a line that is fine to publish, add the comment
`privacy-check: allow` on that line.

## Rules for contributors

- Never commit secrets, signing keys, `.env` files or `local.properties`.
  `.gitignore` blocks the common ones.
- Commit with your GitHub noreply email, not a personal one:
  `git config --global user.email "<id>+<login>@users.noreply.github.com"`
  (find yours under GitHub → Settings → Emails).
- Use paths relative to the repo or the script (`$(dirname "$0")`), never your
  own home folder.
- Do not commit vendor datasheets or anything marked confidential or under
  NDA. Link to the public copy instead.
- Every workflow pins actions to a full commit SHA and starts from
  `permissions: contents: read`.

## Repository settings (owner)

These live in GitHub settings, not in the code, and should stay on:

- Settings → Advanced Security: Dependency graph, Dependabot alerts,
  Dependabot security updates, Secret scanning, **Push protection**,
  Private vulnerability reporting.
- Settings → Branches: protect `main`, require a pull request, and require
  the Security and CodeQL checks to pass.
- Your account → Settings → Emails: **Keep my email address private** and
  **Block command line pushes that expose my email**.
