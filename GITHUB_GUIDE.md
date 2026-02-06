# GitHub Organization & Maintenance Guide

This guide explains how to organize, maintain, and leverage GitHub for the Argo Energy Solutions project.

---

## 📁 Project Structure

```
argo-energy-solutions/
├── .github/
│   └── workflows/              # GitHub Actions automation
│       ├── daily-sync.yml      # Daily data ingestion
│       ├── weekly-report.yml   # Weekly report generation
│       └── data-validation.yml # Data quality checks
├── backend/
│   ├── python_scripts/         # Python data processing
│   │   ├── ingest_to_postgres.py
│   │   ├── generate_customer_report.py
│   │   ├── validate_data.py    # NEW: Data validation
│   │   └── historical_ingestion.py
│   └── scripts/                # Legacy Node.js scripts
├── reports/                    # Generated HTML/JSON reports
├── docs/                       # Project documentation
└── src/                        # Frontend React app
```

---

## 🔄 GitHub Actions Workflows

### 1. Daily Data Sync (`daily-sync.yml`)

**Purpose:** Automatically sync energy data from Eniscope API to Neon database

**Schedule:** Daily at 2 AM UTC (9 PM EST)

**What it does:**
- Fetches last 7 days of data
- Syncs to PostgreSQL database
- Runs data validation checks
- Notifies on failure

**Manual trigger:**
```bash
# Go to: Actions → Daily Energy Data Sync → Run workflow
```

### 2. Weekly Report (`weekly-report.yml`)

**Purpose:** Generate customer-ready weekly reports

**Schedule:** Every Monday at 8 AM UTC (3 AM EST)

**What it does:**
- Generates HTML report with analytics
- Generates JSON report for archival
- Uploads both as artifacts (30-90 days retention)
- Can be configured to email or upload to cloud storage

**Manual trigger:**
```bash
# Go to: Actions → Weekly Energy Report → Run workflow
```

### 3. Data Validation (`data-validation.yml`)

**Purpose:** Continuous data quality monitoring

**Schedule:** Every 6 hours + on code changes

**What it does:**
- Checks schema integrity
- Validates data completeness
- Detects anomalies and outliers
- Creates GitHub issue if validation fails

---

## 🔐 GitHub Secrets Configuration

Before workflows can run, configure these secrets in GitHub:

**Navigate to:** `Settings → Secrets and variables → Actions → New repository secret`

| Secret Name | Value | Description |
|------------|-------|-------------|
| `DATABASE_URL` | `postgresql://user:pass@host/db` | Neon PostgreSQL connection string |
| `VITE_ENISCOPE_API_KEY` | `your-api-key` | Eniscope API key |
| `VITE_ENISCOPE_EMAIL` | `your-email` | Eniscope account email |
| `VITE_ENISCOPE_PASSWORD` | `your-password` | Eniscope account password |

**Get your values from `.env` file** (never commit `.env` to GitHub!)

---

## 📊 Data Validation Checks

### Run Validation Locally

```bash
npm run py:validate
```

### What Gets Validated

1. **Schema Integrity**
   - Verifies all required tables exist
   - Checks timestamp columns use TIMESTAMPTZ
   - Validates foreign key relationships

2. **Data Completeness**
   - Date range coverage
   - Missing days detection
   - Stale channel detection (no data in 24h)

3. **Data Quality**
   - NULL value detection
   - Negative value detection (invalid)
   - Duplicate reading detection
   - Extreme outlier detection

4. **Temporal Continuity**
   - Identifies gaps > 1 hour in time series
   - Per-channel gap analysis

5. **Channel Health**
   - Inactive channel detection
   - Flat reading detection (sensor issues)
   - Reading count per channel

6. **Value Ranges**
   - Power: Should be 0-1000 kW (typical)
   - Voltage: Should be 100-600V
   - Power Factor: Should be -1 to 1

7. **Ingestion Logs**
   - Recent run success rate
   - Failure pattern analysis

### Sample Output

```
🔍 DATA VALIDATION CHECKS
======================================================================

✅ Schema Integrity: PASSED
✅ Data Completeness: 151,742 readings across 17 channels
✅ Data Quality: No NULL or negative values
⚠️  Temporal Continuity: 3 channels with gaps > 1 hour
✅ Channel Health: All 17 channels active
✅ Value Ranges: All within expected bounds
✅ Ingestion Logs: 45/45 successful runs (last 7 days)

📋 VALIDATION SUMMARY
======================================================================
⚠️  WARNINGS (1):
   • Data gaps detected in 3 channels

✅ No critical issues found. Warnings are informational.
```

---

## 🏗️ GitHub Best Practices

### Branch Strategy

**Main Branch Protection:**
```
Settings → Branches → Add rule for 'main'
☑️ Require pull request before merging
☑️ Require status checks to pass (data validation)
☐ Don't require approvals for solo project
```

**Recommended Branches:**
- `main` - Production-ready code
- `dev` - Development work
- `feature/xyz` - New features
- `fix/xyz` - Bug fixes

### Commit Messages

Use clear, descriptive commit messages:

```bash
✅ Good:
git commit -m "Add data validation script with 7 health checks"
git commit -m "Fix: Handle NULL values in power_kw column"
git commit -m "Update daily sync to use 7-day window"

❌ Bad:
git commit -m "updates"
git commit -m "fix bug"
git commit -m "wip"
```

### Pull Request Template

Create `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Data validation passes
- [ ] Analytics tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] No sensitive data in commits
```

---

## 📝 Issue Management

### Issue Labels

Create these labels for organization:

| Label | Color | Purpose |
|-------|-------|---------|
| `bug` | Red | Something isn't working |
| `enhancement` | Blue | New feature or improvement |
| `data-quality` | Yellow | Data validation issues |
| `automated` | Gray | Created by automation |
| `documentation` | Green | Documentation updates |
| `urgent` | Orange | Requires immediate attention |

### Issue Templates

Create `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug Report
about: Report a bug or issue
labels: bug
---

## Description
Clear description of the bug

## Steps to Reproduce
1. Run command: `npm run xyz`
2. See error: ...

## Expected Behavior
What should happen

## Actual Behavior
What actually happened

## Environment
- Date: 
- Data range affected:
- Error logs:
```

---

## 🔄 Maintenance Workflow

### Daily Tasks (Automated)
- ✅ Data sync runs automatically
- ✅ Validation checks run every 6 hours
- 👀 Check GitHub Actions for failures

### Weekly Tasks
- 📧 Review weekly report
- 🔍 Check data validation warnings
- 📊 Monitor ingestion logs

### Monthly Tasks
- 🗄️ Archive old reports
- 📈 Review data growth trends
- 🔧 Update dependencies
- 📝 Update documentation

### Quarterly Tasks
- 🎯 Review project goals
- 🧪 Comprehensive testing
- 🏗️ Refactoring opportunities
- 📚 Major documentation updates

---

## 📦 Release Management

### Semantic Versioning

Follow semver (MAJOR.MINOR.PATCH):

```bash
# Bug fix (1.0.0 → 1.0.1)
git tag -a v1.0.1 -m "Fix NULL value handling"

# New feature (1.0.1 → 1.1.0)
git tag -a v1.1.0 -m "Add data validation script"

# Breaking change (1.1.0 → 2.0.0)
git tag -a v2.0.0 -m "Migrate to Python-only architecture"

git push origin --tags
```

### Release Checklist

- [ ] All tests pass
- [ ] Data validation passes
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in package.json
- [ ] Git tag created
- [ ] GitHub Release created with notes

---

## 🔒 Security Best Practices

### Never Commit Secrets

Already configured in `.gitignore`:
```
.env
*.key
*.pem
credentials.json
```

### Rotate Secrets Regularly

Every 3-6 months:
1. Generate new API keys in Eniscope portal
2. Update GitHub Secrets
3. Update local `.env` file
4. Verify workflows still work

### Audit Access

Regularly review:
- GitHub repository access
- Neon database users
- API key usage logs

---

## 📊 Monitoring & Alerts

### GitHub Actions Monitoring

**View workflow status:**
```
https://github.com/YOUR_USERNAME/argo-energy-solutions/actions
```

**Set up email notifications:**
```
Settings → Notifications → GitHub Actions
☑️ Send notifications for workflow runs on repositories you watch
```

### Database Monitoring (Neon)

**Dashboard:** https://console.neon.tech/

Monitor:
- Database size (watch for 10GB free tier limit)
- Query performance
- Active connections
- Error logs

### Set Up Status Page (Optional)

Use GitHub Pages to show system status:

```yaml
# .github/workflows/status-page.yml
name: Update Status Page

on:
  schedule:
    - cron: '*/15 * * * *' # Every 15 minutes

jobs:
  update-status:
    runs-on: ubuntu-latest
    steps:
      - name: Check API status
        run: curl -f https://core.eniscope.com || exit 1
      
      - name: Check database
        run: # Add database health check
      
      - name: Update status badge
        # Generate status badge and commit to gh-pages branch
```

---

## 🚀 Quick Start Commands

### Development

```bash
# Install dependencies
npm install
pip install -r backend/python_scripts/requirements.txt

# Run data validation
npm run py:validate

# Generate test report
npm run py:report:customer

# Run all analytics tests
npm run py:test

# Sync latest data
npm run py:ingest
```

### Deployment

```bash
# Push to GitHub (triggers validation workflow)
git add .
git commit -m "Descriptive message"
git push origin main

# Manual workflow trigger
gh workflow run daily-sync.yml
gh workflow run weekly-report.yml
gh workflow run data-validation.yml
```

### Troubleshooting

```bash
# Check recent workflow runs
gh run list

# View specific run logs
gh run view <run-id>

# Download report artifacts
gh run download <run-id>

# Check database status
npm run py:validate

# View ingestion logs
npm run py:logs
```

---

## 📚 Additional Resources

### GitHub Actions Documentation
- [Workflow syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Secrets management](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Artifact management](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)

### Project Documentation
- [Neon Setup Guide](docs/setup/NEON_SETUP_GUIDE.md)
- [Customer Reports Guide](CUSTOMER_REPORTS_GUIDE.md)
- [Python Migration Complete](PYTHON_MIGRATION_COMPLETE.md)
- [Testing Complete](TESTING_COMPLETE.md)

### Related Tools
- [GitHub CLI](https://cli.github.com/) - Command-line GitHub management
- [Act](https://github.com/nektos/act) - Run GitHub Actions locally
- [Neon Console](https://console.neon.tech/) - Database management

---

## 🤝 Contributing

This is a personal project, but following these guidelines will keep it maintainable:

1. **Test before committing**: Run `npm run py:validate` and `npm run py:test`
2. **Document changes**: Update relevant docs with new features
3. **Keep secrets safe**: Never commit `.env` or credentials
4. **Use branches**: Work on features in separate branches
5. **Write clear commits**: Describe what and why, not how
6. **Review workflows**: Check Actions tab for any failures

---

## 📞 Support & Contact

**Issues:** Use GitHub Issues for bug reports and feature requests

**Documentation:** Check `/docs` folder for guides

**Quick Reference:** See [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)

---

**Last Updated:** February 2026
