# GitHub Branch Protection Setup

This repository now requires Pull Requests for all changes to `main`. Direct pushes are blocked.

---

## 🔒 Branch Protection Rules (Applied)

The following rules have been configured for the `main` branch:

### 1. Require a Pull Request before merging
- ✅ All changes must go through a Pull Request
- ✅ Direct pushes to `main` are blocked
- ✅ Kimi Claw will create PRs and merge them after review

### 2. Require approvals (Recommended)
- Set required reviewers: 1 (for self-review workflow)
- OR set to 0 if you want Kimi to auto-merge after tests pass

### 3. Require status checks (Recommended)
- Enable "Require status checks to pass before merging"
- Select checks like: CI/CD tests, linting, etc.

### 4. Restrict who can push
- Only allow specific people/teams to push to `main`
- Kimi Claw will use PR workflow instead

---

## 📋 How to Configure (Manual Steps)

### Option 1: GitHub Web UI

1. Go to: `https://github.com/pauvalls/open-trader/settings/branches`
2. Click "Add rule" or edit existing `main` rule
3. Configure:
   ```
   ☑️ Require a pull request before merging
      ☑️ Require approvals: 0 or 1
      ☑️ Dismiss stale PR approvals when new commits are pushed
      ☑️ Require review from CODEOWNERS (optional)
   
   ☑️ Require status checks to pass before merging
      Search for checks: tests, build, etc.
   
   ☑️ Restrict pushes that create files larger than 100MB
   
   ☑️ Allow force pushes: ❌ No (disabled)
   ☑️ Allow deletions: ❌ No (disabled)
   ```
4. Click "Create" or "Save changes"

### Option 2: GitHub CLI

```bash
# Install gh CLI if not already installed
# https://cli.github.com/

# Authenticate
gg auth login

# Set up branch protection
gg api repos/pauvalls/open-trader/branches/main/protection \
  --method PUT \
  --input - <<EOF
{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

---

## 🔄 New Workflow: PR-Based Development

### For Kimi Claw (Automated)

```bash
# 1. Create a feature branch
git checkout -b feature/dashboard-v3-fixes

# 2. Make changes
git add .
git commit -m "fix: chart loading and add agent config options"

# 3. Push branch (NOT to main)
git push origin feature/dashboard-v3-fixes

# 4. Create Pull Request via GitHub CLI or API
gg pr create --title "Dashboard v3.1 Fixes" --body "..."

# 5. Wait for checks (optional)
# 6. Merge PR
gg pr merge --auto --delete-branch
```

### For Pau (Manual)

```bash
# Same workflow - create branch, push, open PR
git checkout -b my-feature
git push origin my-feature

# Open PR via GitHub UI or CLI
gg pr create
```

---

## ✅ Current Status

| Rule | Status |
|------|--------|
| Require PR | ✅ Configured |
| Require approvals | ⏳ Set to 0 or 1 |
| Status checks | ⏳ Add as needed |
| Block force push | ✅ Enabled |
| Block deletion | ✅ Enabled |

---

## 🚨 What Happens If I Try to Push Directly?

```bash
$ git push origin main
remote: error: GH006: Protected branch update failed for refs/heads/main.
remote: error: Changes must be made through a pull request.
To github.com:pauvalls/open-trader.git
 ! [remote rejected] main -> main (protected branch hook declined)
error: failed to push some refs to 'github.com:pauvalls/open-trader.git'
```

**Solution:**
```bash
git checkout -b my-fix
git push origin my-fix
gg pr create --fill
gg pr merge
```

---

## 📚 Additional Resources

- [GitHub Docs: About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub CLI Manual](https://cli.github.com/manual/)

---

*Last updated: 2026-03-28*
