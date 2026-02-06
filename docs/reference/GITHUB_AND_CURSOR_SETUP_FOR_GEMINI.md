# GitHub and Cursor Setup — Full Breakdown for Gemini

This document explains how **GitHub** and **Cursor IDE** are set up for this work: the **cursor-repo** structure, where **argo-energy-solutions** lives, how Cursor is used, and how to reason about paths and context when working with Gemini (or any AI).

---

## 1. High-level: one repo, many projects

- **Single Git repository:** Everything lives in one repo called **cursor-repo** (GitHub: `samargo3/cursor-repo`).
- **Monorepo layout:** The repo root is the Git root. There is **no separate Git repository** for argo-energy-solutions; it is a **subfolder** inside the repo.
- **Projects folder:** All “projects” (applications, demos, client work) live under **`projects/`**. Argo Energy Solutions is one of them.

So when we say “the argo-energy-solutions project,” we mean the **directory**  
`cursor-repo/projects/argo-energy-solutions/`  
inside the **cursor-repo** Git repository.

---

## 2. Repository identity and location

| What | Value |
|------|--------|
| **Repository name** | cursor-repo |
| **GitHub URL** | https://github.com/samargo3/cursor-repo |
| **Local path (typical)** | `/Users/sargo/cursor-repo` |
| **Git root** | `/Users/sargo/cursor-repo` (single root for the whole repo) |
| **Default branch** | main |
| **Argo Energy Solutions path** | `projects/argo-energy-solutions/` (relative to repo root) |
| **Argo full path** | `/Users/sargo/cursor-repo/projects/argo-energy-solutions` |

All commits for cursor-repo (including changes under `projects/argo-energy-solutions/`) are made from this single Git repository. There is no nested `.git` inside argo-energy-solutions.

---

## 3. Cursor repo directory structure

What lives at the **root** of cursor-repo (one level above argo-energy-solutions):

```
cursor-repo/                          ← Git root; open "cursor-repo" here to see everything
├── .git/                             ← Single Git repo (entire monorepo)
├── .gitignore                        ← Root ignore (node_modules, .env, .sfdx, dist, etc.)
├── cursor-repo.code-workspace        ← Multi-root workspace definition (see below)
├── README.md                         ← Repo overview, purpose, projects list
├── QUICK_START.md                    ← How to open repo and common commands
├── SETUP_GUIDE.md                    ← Setup, new projects, shared configs, GitHub
│
├── documentation/                    ← Repo-wide docs (MCPs, workflows, troubleshooting)
│   ├── README.md
│   └── mcps/
│       └── configured-mcps.md        ← List of MCPs (browser, GitHub, Tableau, etc.)
│
├── projects/                         ← All projects live here
│   ├── argo-energy-solutions/        ← This project (Node/React/Python, energy platform)
│   ├── Agentforce Contract Analysis/
│   ├── demo-igniters/                ← Salesforce demo (sometimes has its own .git; see SETUP_GUIDE)
│   ├── My Sandbox/
│   ├── Pizza Chart Project/
│   ├── project-data-pipeline/
│   └── ...
│
├── scripts/                          ← Repo-level automation
│   └── setup-new-project.sh          ← Creates new project + optional symlinks to shared configs
│
└── shared-configs/                   ← Shared Cursor/VSCode config (reusable across projects)
    ├── README.md
    ├── cursor-rules/                 ← Shared AI rules (Salesforce Apex, LWC, UI/UX)
    │   ├── salesforce-apex-standards.md
    │   ├── salesforce-lwc-best-practices.md
    │   └── salesforce-ui-ux-standards.md
    └── vscode/                       ← VSCode/Cursor settings templates
        ├── salesforce-settings.json
        └── salesforce-extensions.json
```

Important for Gemini:

- **Paths in conversation:** When the user has Cursor opened at **argo-energy-solutions**, the **workspace root** is often  
  `.../cursor-repo/projects/argo-energy-solutions`.  
  So paths like `src/App.tsx` or `backend/python_scripts/ingest/ingest_to_postgres.py` are **relative to that project folder**, not the repo root.
- **Repo root paths:** If the user opens the **whole cursor-repo** folder, then the workspace root is  
  `.../cursor-repo`,  
  and argo-energy-solutions is at  
  `projects/argo-energy-solutions/`.
- **Absolute paths:** The repo root is `/Users/sargo/cursor-repo`; the project root is `/Users/sargo/cursor-repo/projects/argo-energy-solutions`.

---

## 4. How Cursor is opened (two common ways)

The user can work in two main ways. **Which folder is “open” determines the workspace root and relative paths.**

### 4.1 Option A: Open the full cursor-repo (root)

- **Command:** `cursor ~/cursor-repo` (or open folder `/Users/sargo/cursor-repo`).
- **Workspace root:** `cursor-repo/`.
- **Implications:**
  - Search and file picker see **all** projects (argo-energy-solutions, demo-igniters, etc.).
  - Relative paths from the workspace root: e.g. `projects/argo-energy-solutions/package.json`, `projects/argo-energy-solutions/src/App.tsx`.
  - Good for: cross-project search, editing shared-configs or documentation, working on multiple projects in one window.

### 4.2 Option B: Open only the argo-energy-solutions project

- **Command:** `cursor ~/cursor-repo/projects/argo-energy-solutions`.
- **Workspace root:** `projects/argo-energy-solutions/` (i.e. the project folder).
- **Implications:**
  - Cursor’s “workspace” is just this project. Paths like `src/App.tsx`, `backend/python_scripts/ingest/ingest_to_postgres.py`, `docs/reference/NEON_DATABASE_BREAKDOWN_FOR_GEMINI.md` are **relative to this folder**.
  - The parent cursor-repo (shared-configs, documentation, other projects) is **not** inside the workspace; it’s one level up.
  - This is the setup reflected in “Workspace Path: .../cursor-repo/projects/argo-energy-solutions” in Cursor metadata.

**For Gemini:** Prefer **project-relative paths** (e.g. `backend/python_scripts/govern/validate_data.py`) when the user is working in argo-energy-solutions. If they mention “repo root” or “cursor-repo,” use paths relative to `cursor-repo/` (e.g. `projects/argo-energy-solutions/...`).

---

## 5. Multi-root workspace file (cursor-repo.code-workspace)

Opening **`cursor-repo.code-workspace`** gives a **multi-root workspace** (several folders in one Cursor window):

- **Folder 1:** `"."` — cursor-repo root (name: “🏠 Cursor Repo (Root)”).
- **Folder 2:** `shared-configs` — shared Cursor rules and VSCode config.
- **Folder 3:** `documentation` — repo documentation.
- **Folder 4:** `projects/demo-igniters` — Demo Igniters project.

**Note:** **argo-energy-solutions is not** currently one of the workspace roots in this file. So when the user works on argo-energy-solutions, they typically either:

- Open the **root** `cursor-repo` (Option A) and navigate to `projects/argo-energy-solutions/`, or  
- Open the **folder** `projects/argo-energy-solutions` directly (Option B).

The workspace file also sets:

- **files.exclude:** `.git`, `.DS_Store`, `node_modules`, `.sfdx` (hidden from file tree).
- **search.exclude:** `node_modules`, `.sfdx`, `bower_components`.
- **extensions.recommendations:** Salesforce DX, Prettier, ESLint.

---

## 6. Argo-energy-solutions as a project inside cursor-repo

### 6.1 Role in the repo

- **Location:** `projects/argo-energy-solutions/`.
- **Type:** Node.js/TypeScript (React, Vite) + Python (ingestion, analytics, reports); energy monitoring and analytics platform.
- **Git:** No nested `.git`; it is part of cursor-repo. All version control is at the repo root.

### 6.2 Project-local config (no shared symlinks by default)

- **.gitignore:** Project has its own `.gitignore` (node_modules, .env, build outputs, etc.); root `.gitignore` also applies.
- **.cursor:** There is **no** `.cursor` folder (e.g. no `.cursor/rules`) inside argo-energy-solutions in the repo. So this project does **not** currently use the shared cursor-rules symlink that `setup-new-project.sh` creates for new Node/Salesforce projects.
- **.github:** Project has its own `.github/workflows/` (e.g. daily-sync, data-validation, weekly-report). Those workflows run in the context of the **cursor-repo** repo (same Git repo).

### 6.3 Paths when working in this project

When the workspace root is **argo-energy-solutions**:

- **Frontend:** `src/`, `src/App.tsx`, `src/pages/Dashboard.tsx`, etc.
- **Backend:** `backend/server/`, `backend/scripts/`, `backend/python_scripts/` (e.g. `backend/python_scripts/ingest/ingest_to_postgres.py`, `backend/python_scripts/govern/validate_data.py`).
- **Docs:** `docs/`, `docs/reference/`, `docs/setup/`, etc.
- **Config:** `package.json`, `vite.config.ts`, `tsconfig.json`, `.env.example` (and local `.env` at project root).

When the workspace root is **cursor-repo**:

- Same files are under **`projects/argo-energy-solutions/...`** (e.g. `projects/argo-energy-solutions/package.json`).

---

## 7. Shared configurations (shared-configs)

- **Purpose:** Reusable Cursor rules and VSCode settings across projects in cursor-repo.
- **Location:** `cursor-repo/shared-configs/` (relative to repo root).

### 7.1 cursor-rules

- **Path:** `shared-configs/cursor-rules/`.
- **Contents:** Markdown files that define AI behavior (e.g. Salesforce Apex standards, LWC best practices, UI/UX standards). Used so Cursor (and thus Gemini, when given this context) can follow the same conventions across Salesforce projects.
- **Use in a project:** New projects created with `scripts/setup-new-project.sh` get `.cursor/rules` and a **symlink** `shared` → `../../shared-configs/cursor-rules` (from the project’s `.cursor/rules/`). Argo-energy-solutions was not necessarily created with that script, so it may not have this link; it can be added manually if desired.

### 7.2 vscode

- **Path:** `shared-configs/vscode/`.
- **Contents:** `salesforce-settings.json`, `salesforce-extensions.json` (templates for Salesforce projects). Node.js projects created with the setup script get a basic structure; argo-energy-solutions has its own `.vscode` or relies on root/editor defaults.

### 7.3 For Gemini

- Shared rules apply mainly to **Salesforce** projects (Apex, LWC). For **argo-energy-solutions**, the main “rules” and context are in the project’s own docs (e.g. `docs/reference/ARGO_ENERGY_SOLUTIONS_PROJECT_CONTEXT_FOR_GEMINI.md`, `NEON_DATABASE_BREAKDOWN_FOR_GEMINI.md`) and codebase structure, not in shared-configs.

---

## 8. Creating new projects (scripts/setup-new-project.sh)

- **Location:** `cursor-repo/scripts/setup-new-project.sh`.
- **Usage:** `./scripts/setup-new-project.sh <type> <name>` from repo root.
- **Types:** `salesforce`, `nodejs` (and possibly `python` in usage message; script implements salesforce and nodejs).
- **Behavior:**
  - Creates `projects/<name>/`.
  - For **salesforce:** runs `sfdx project generate`, creates `.cursor/rules` and symlink to `shared-configs/cursor-rules`, copies VSCode Salesforce settings.
  - For **nodejs:** creates `src/`, `tests/`, `.cursor/rules`, `npm init -y`, and symlink to shared cursor-rules.
- **Argo-energy-solutions:** Was likely added by copying or moving an existing project into `projects/`, not by this script, so it doesn’t have the same `.cursor/rules` symlink or template layout.

---

## 9. Root .gitignore (cursor-repo)

Applies to the **entire** repo (including argo-energy-solutions):

- **OS:** `.DS_Store`, `Thumbs.db`, `*.swp`
- **Dependencies:** `node_modules/`, `.pnp`, `.pnp.js`
- **Secrets/env:** `.env`, `.env.local`, `.env.*.local`, `*.key`, `*.pem`
- **Salesforce:** `.sfdx/`, `.localdevserver/`, `.sf/`
- **Build:** `dist/`, `build/`, `*.log`, `.cache/`
- **IDE:** `.idea/`, `*.code-workspace.bak`
- **Testing:** `coverage/`, `.nyc_output/`
- **Misc:** `*.bak`, `*.tmp`, `.temp/`

Project-specific ignores (e.g. `venv/`, `reports/*.html`) can be in `projects/argo-energy-solutions/.gitignore` and are additive.

---

## 10. Cursor IDE project metadata (when opened at argo-energy-solutions)

When the user opens Cursor with **workspace path**  
`/Users/sargo/cursor-repo/projects/argo-energy-solutions`,  
Cursor stores project-specific data under a path like:

`~/.cursor/projects/Users-sargo-cursor-repo-projects-argo-energy-solutions/`

Typical contents:

- **terminals/** — Terminal session state (e.g. cwd, last commands).
- **agent-tools/, agent-transcripts/** — Agent/tool runs and transcripts.
- **mcps/** — Metadata for MCPs **available in this project** (cursor-ide-browser, user-github, user-Neon, user-tableau, etc.). These are **user-level** MCPs; they are configured once and appear when working in any project, including argo-energy-solutions.

So: **Git** is one repo (cursor-repo). **Cursor** can be opened at repo root or at `projects/argo-energy-solutions`; the “project” in Cursor’s sense is the opened folder, and MCPs (GitHub, Neon, Tableau, browser) apply in that context.

---

## 11. MCPs (Model Context Protocol) — user-level

Documented in `cursor-repo/documentation/mcps/configured-mcps.md`. These are configured at the **user level** in Cursor and are available when working in **any** project, including argo-energy-solutions:

| MCP | Purpose |
|-----|--------|
| **cursor-ide-browser** | Browser automation for frontend testing. |
| **cursor-browser-extension** | Additional browser capabilities for webapp testing. |
| **user-github** | GitHub (issues, PRs, repos, search, file contents, etc.). |
| **user-tableau** | Tableau (datasources, views, workbooks, Pulse, etc.). |
| **user-Neon** (or similar) | Neon DB (projects, branches, SQL, migrations, query tuning, etc.). |

A **project-specific** Salesforce MCP is started from `projects/demo-igniters` (`npm run mcp:start`); it is **not** used for argo-energy-solutions. For argo-energy-solutions, the relevant MCPs are GitHub, Tableau, and Neon (and browser if doing front-end work).

---

## 12. Summary for Gemini: how to reason about paths and context

1. **Single repo:** All of cursor-repo (including argo-energy-solutions) is one Git repo: `samargo3/cursor-repo`. There is no separate GitHub repo for “argo-energy-solutions” by default; it’s a folder in that repo.

2. **Two possible workspace roots:**
   - **Repo root:** `cursor-repo/` → argo paths start with `projects/argo-energy-solutions/`.
   - **Project root:** `projects/argo-energy-solutions/` → argo paths are relative to that folder (e.g. `src/App.tsx`, `backend/python_scripts/ingest/ingest_to_postgres.py`). Prefer these when the user is “in” the argo project.

3. **Argo-energy-solutions** = `projects/argo-energy-solutions/` in cursor-repo. It contains its own package.json, backend, docs, .github workflows, and .env.example; it does not have its own .git or .cursor/rules in the repo.

4. **Shared config:** Lives in `cursor-repo/shared-configs/` (cursor-rules, vscode). Used mainly by other projects (e.g. Salesforce); argo’s primary context is its own docs and code.

5. **Git operations:** Run from repo root (`/Users/sargo/cursor-repo`). Changes under `projects/argo-energy-solutions/` are committed and pushed as part of cursor-repo.

6. **MCPs:** User-level GitHub, Tableau, Neon (and browser) are available when the user has Cursor opened at argo-energy-solutions; use them for GitHub actions, Tableau assets, and Neon DB operations in this project.

---

This document, together with **ARGO_ENERGY_SOLUTIONS_PROJECT_CONTEXT_FOR_GEMINI.md** and **NEON_DATABASE_BREAKDOWN_FOR_GEMINI.md**, gives Gemini full context on: the GitHub/cursor-repo layout, how Cursor is opened, where argo-energy-solutions sits, and how paths and tools (MCPs) should be used.
