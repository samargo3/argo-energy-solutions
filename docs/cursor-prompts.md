# Argo Energy Solutions — Cursor Prompt Templates

> Reference library of task-specific prompts to paste into Cursor chat.
> These complement the always-active rules in `.cursor/rules/argo-governance.mdc`.
> Keep this file updated as the codebase evolves.
>
> Last updated: 2026-02-15

---

## How to Use

1. Find the prompt that matches your task below.
2. Copy the entire prompt block.
3. Paste it into Cursor chat at the start of your session.
4. Fill in the bracketed placeholders before sending.

The `.cursor/rules/argo-governance.mdc` rules are always active in the background —
these prompts add task-specific context on top of them.

---

## Prompt A — New Script or Feature

Use when: Adding any new Python script or significant new capability to the pipeline.
```
I'm adding a new script/feature to Argo Energy Solutions.
Stage: [Ingest / Govern / Analyze / Deliver]
Purpose: [one sentence description]
Inputs: [what data or parameters it takes]
Outputs: [what it produces — DB writes, files, return values]
Before writing any code, please:

Confirm this belongs to the stated stage and explain why.
Identify which Layer 3 views it should consume (if Analyze/Deliver).
Check whether validate_data.py or check_completeness.py needs updating.
Confirm whether a new npm run py:* command is needed.
Draft the CHANGELOG.md entry I should add.

Then write the script following all argo-governance.mdc rules.
```

---

## Prompt B — Schema Migration

Use when: Adding columns, creating tables, adding indexes, or modifying any database structure.
```
I need to make a database schema change for Argo Energy Solutions.
Change: [describe the ALTER TABLE / CREATE TABLE / CREATE INDEX]
Reason: [why this change is needed]
Affected tables/views: [list them]
Before writing any SQL, please:

Confirm this belongs in python_scripts/govern/ as a migration script.
Make the script fully idempotent (IF NOT EXISTS, ON CONFLICT DO NOTHING).
Identify any Layer 3 views that need to be recreated or updated after this migration.
Confirm whether refresh_views.py needs to be run after.
Draft the npm run command to invoke this migration.
Draft the CHANGELOG.md entry.

Write the migration script and any view updates needed.
```

---

## Prompt C — Modifying a GitHub Actions Workflow

Use when: Changing any file in .github/workflows/.
Note: workflow-changes.mdc will also auto-activate when these files are open.
```
I need to modify a GitHub Actions workflow for Argo Energy Solutions.
Workflow: [filename]
Change: [describe what you want to change]
Reason: [why]
This is a HIGH-RISK change. Before writing anything, please:

Identify what production behaviour this workflow currently provides.
Confirm the data-validation circuit breaker step is preserved.
Check that all secrets use ${{ secrets.SECRET_NAME }} format.
Describe the failure behaviour if this workflow errors — what gets skipped?
Suggest how to test this safely (manual workflow_dispatch run before merging).
Draft the CHANGELOG.md entry.

Then make the minimal change needed.
```

---

## Prompt D — Adding a New Customer Site

Use when: Onboarding a new Eniscope site into the platform.
```
I'm onboarding a new customer site to Argo Energy Solutions.
Site name: [name]
Eniscope site ID: [ID]
Timezone: [e.g. America/New_York]
Channels to monitor: [list known channels or "unknown — need to discover"]
Please walk me through the full onboarding checklist:

The SQL to register this site in the sites table.
The command to run a historical backfill and what date range to use.
How to verify the ingested data looks complete and correct.
What to add/update in validate_data.py and check_completeness.py.
How to confirm the site appears in npm run py:sites.
What to update in docs/PROJECT_CONTEXT.md.
The CHANGELOG.md entry.

Generate the SQL and any script changes needed.
```

---

## Prompt E — Debugging a Pipeline Failure

Use when: The daily sync, validation, or a report has failed or produced unexpected output.
```
A pipeline step in Argo Energy Solutions has failed or produced unexpected output.
Failed step: [daily sync / validation / report generation / specific script name]
Symptom: [what you observed — error message, missing data, wrong values]
When noticed: [date and time approximately]
Please help me debug this systematically:

Identify which stage (Ingest/Govern/Analyze/Deliver) the failure most likely originates in.
List the specific log files or database tables I should check first.
Suggest the npm run commands I can use to isolate the problem.
Identify whether the validation circuit breaker caught this or passed it through.
Once root cause is found, confirm the fix maintains idempotency and doesn't weaken validation.
```

---

## Prompt F — Updating Configuration Values

Use when: Changing any threshold, rate, or parameter in the config/ folder.
```
I need to update a configuration value in Argo Energy Solutions.
File: config/[filename]
Value changing: [parameter name]
Old value: [old]
New value: [new]
Reason: [e.g. new utility tariff effective DATE, customer request, threshold review]
Before making the change:

Show me the current value and any existing comment on it.
Write the updated comment in the format: # [YYYY-MM-DD] Source: <reason>
Check if this value is referenced in any analyze/ or deliver/ scripts that may need review.
Draft the CHANGELOG.md entry.
Flag if this change could affect any active customer reports or anomaly detection thresholds.
```

---

## Prompt G — Monthly Health Review

Use when: Doing a periodic infrastructure review. Run this once a month.
```
Please conduct a health review of the Argo Energy Solutions infrastructure.
Review the following and give me a status on each:

docs/PROJECT_CONTEXT.md — is it current with the actual codebase? Flag any sections that look stale.
CHANGELOG.md — are there recent entries? When was it last updated?
.cursor/rules/argo-governance.mdc — do the rules still reflect how the codebase actually works?
GitHub Actions workflows — are there any workflows that haven't run recently or have a history of failures?
config/ — are there any configuration values without a dated comment?
govern/ — are there any migration scripts that aren't idempotent?
python_scripts/ — are there any scripts that don't have a corresponding npm run py:* command?

For each issue found, suggest the minimal fix.
```

---

## Maintenance Notes

- When a new convention is established, update `argo-governance.mdc` AND add a note here.
- When a new script type is added regularly, consider adding a new prompt for it.
- Review and update the workflow impact table in `workflow-changes.mdc` if workflows are added or removed.
