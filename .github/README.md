# GitHub Workflows

This folder contains GitHub Actions workflows for automation.

## Active Workflows

### `daily-sync.yml`
- **Schedule:** Daily at 2 AM UTC (9 PM EST)
- **Purpose:** Sync energy data from Eniscope to Neon
- **Duration:** ~5 minutes
- **Triggers:** Schedule + manual

### `weekly-report.yml`
- **Schedule:** Every Monday at 8 AM UTC (3 AM EST)
- **Purpose:** Generate customer-ready reports
- **Duration:** ~10 minutes
- **Outputs:** HTML + JSON reports (artifacts)
- **Triggers:** Schedule + manual

### `data-validation.yml`
- **Schedule:** Every 6 hours + on code changes
- **Purpose:** Data quality monitoring
- **Duration:** ~3 minutes
- **Triggers:** Schedule + push to main + manual
- **Alert:** Creates GitHub issue on failure

## Setup Required

**Before workflows can run, configure GitHub Secrets:**

Navigate to: `Settings → Secrets and variables → Actions`

Add these 4 secrets:
1. `DATABASE_URL` - Your Neon connection string
2. `VITE_ENISCOPE_API_KEY` - Eniscope API key
3. `VITE_ENISCOPE_EMAIL` - Eniscope account email
4. `VITE_ENISCOPE_PASSWORD` - Eniscope account password

Get values from your local `.env` file (never commit `.env`!)

## Manual Triggers

**Via GitHub UI:**
1. Go to: `Actions` tab
2. Select workflow
3. Click "Run workflow"
4. Choose branch (usually `main`)
5. Click "Run workflow"

**Via GitHub CLI:**
```bash
gh workflow run daily-sync.yml
gh workflow run weekly-report.yml
gh workflow run data-validation.yml
```

## Monitoring

**Check workflow status:**
```bash
gh run list --limit 10

# View specific run
gh run view <run-id>

# Download artifacts
gh run download <run-id>
```

**Email notifications:**
`Settings → Notifications → GitHub Actions`
- ☑️ Send notifications for failed workflow runs

## Troubleshooting

**"Workflow failed"**
→ Check logs in Actions tab
→ Verify secrets are configured
→ Test command locally first

**"No artifacts found"**
→ Check workflow completed successfully
→ Artifacts expire after 30-90 days
→ Download immediately after generation

**"Rate limit exceeded"**
→ Eniscope API has rate limits
→ Workflows include 1s delays
→ Check if multiple workflows running simultaneously

---

For detailed documentation, see: [GITHUB_GUIDE.md](../GITHUB_GUIDE.md)
