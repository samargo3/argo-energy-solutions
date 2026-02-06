# Neon MCP Troubleshooting

Use this guide when the **Neon MCP** in Cursor shows an error or doesn’t work as expected.

---

## Log shows "Streamable HTTP" / "SSE 404" / "OAuth scopes: api, sfap_api..."

**Symptom:** Log says `Creating streamableHttp transport`, `Using OAuth scopes: api, sfap_api...`, `Error POSTing to endpoint:`, `SSE error: Non-200 status code (404)`, `No stored tokens found`.

**Cause:** Neon is configured as an **HTTP/SSE** (or “Streamable HTTP”) server. Cursor is trying to connect to a URL with OAuth (Salesforce-style). The Neon MCP is **command-based**: Cursor must run `npx @neondatabase/mcp-server-neon` and talk over stdin/stdout.

**Fix:**

1. Open **Cursor Settings** → **Features** → **MCP** (or **MCP Servers**).
2. Find the **Neon** server.
3. Change the **type** to **Command** (not “SSE”, “Streamable HTTP”, or “URL”).
4. Set:
   - **Command:** `npx`
   - **Arguments:** `-y`, `@neondatabase/mcp-server-neon`
   - **Env:** add `NEON_API_KEY` = your key from [Neon API Keys](https://console.neon.tech/app/settings/api-keys)
5. Remove any **URL** or **endpoint** field (Neon doesn’t use one).
6. Save and restart Cursor (or disable then re-enable the Neon MCP).

After this, the log should show Cursor starting a **command** process, not “streamableHttp” or “SSE”.

---

## 1. Check how Neon MCP is configured

Neon MCP is configured in **Cursor** (user-level), not in this repo.

- **Cursor Settings** → **Features** → **MCP** (or **MCP Servers**)
- Find the **Neon** (or “Neon MCP”) server entry.

It should look like this:

| Field   | Value |
|--------|--------|
| **Type** | `command` (not `sse`) |
| **Command** | `npx` |
| **Arguments** | `-y`, `@neondatabase/mcp-server-neon` (or `-y`, `@neondatabase/mcp-server-neon`, `start`) |
| **Env** | `NEON_API_KEY` = your API key |

**Correct JSON-style config (for reference):**

The **local** (stdio) Neon MCP server requires the API key as a **command-line argument** after `start`, not only in env. Use:

```json
{
  "mcpServers": {
    "Neon": {
      "command": "npx",
      "args": ["-y", "@neondatabase/mcp-server-neon", "start", "YOUR_NEON_API_KEY"]
    }
  }
}
```

Replace `YOUR_NEON_API_KEY` with your key from [Neon API Keys](https://console.neon.tech/app/settings/api-keys).  
If you use only `args: ["-y", "@neondatabase/mcp-server-neon"]` and `env.NEON_API_KEY`, the server can print **"Invalid number of arguments"** and colored error text to stdout, which breaks the MCP protocol.

- Get the API key: **[Neon Console → Account → API Keys](https://console.neon.tech/app/settings/api-keys)** (create one if needed).
- Do **not** put your database connection string (`DATABASE_URL`) in the MCP config; the MCP uses the **API key** to talk to Neon’s API and run SQL on your project.

---

## 2. Common errors and fixes

### “No tools” or MCP shows no tools

- **Cause:** MCP can’t start or can’t see the Neon tools; often the API key is missing or wrong.
- **Fix:**
  1. In Cursor MCP config, set **Env** → `NEON_API_KEY` to your key from [Neon API Keys](https://console.neon.tech/app/settings/api-keys).
  2. Restart Cursor (or disable/re-enable the Neon MCP server).
  3. Confirm the server type is **command** and the command is `npx` with args `-y`, `@neondatabase/mcp-server-neon`.

### “NEON_API_KEY not set” / “API key required”

- **Cause:** The MCP is started without `NEON_API_KEY` in its environment.
- **Fix:** In Cursor MCP config, add **Env** and set `NEON_API_KEY` to your Neon API key (same as above). Save and restart the MCP / Cursor.

### 404 on `run_sql` or `get_database_tables`

- **Cause:** Some Cursor/Neon MCP versions have had 404s on database operations even with a valid key; `list_projects` may still work.
- **Fix:**
  1. Update the MCP: in terminal run  
     `npx -y @neondatabase/mcp-server-neon --version`  
     (or check for updates to `@neondatabase/mcp-server-neon`).
  2. When asking the AI to run SQL, **specify the project name** (e.g. the Neon project that contains `neondb`), not only “my Neon DB”.
  3. If it keeps failing, use your project’s **direct DB workflow** instead: `npm run db:views`, `npm run db:refresh-views`, or scripts that use `DATABASE_URL`; those don’t use the MCP.

### MCP “stuck” or slow on listing projects

- **Cause:** Calling something like “list all my Neon projects” without a project name can be slow or get stuck.
- **Fix:** When using the Neon MCP, **specify the project/branch/database** (e.g. project name and branch that your `.env` `DATABASE_URL` uses) so the MCP doesn’t have to enumerate everything.

### Connection / timeout errors

- **Cause:** Network, firewall, or Neon API temporarily unavailable.
- **Fix:**
  1. Check [Neon Status](https://status.neon.tech/) and your network.
  2. Confirm the API key has not been revoked in [Neon API Keys](https://console.neon.tech/app/settings/api-keys).
  3. Retry; if it persists, use `DATABASE_URL` and your existing scripts (`npm run db:views`, etc.) instead.

### “Cannot find module” or command not found

- **Cause:** `npx` can’t find `@neondatabase/mcp-server-neon` (e.g. Node/npm path or version).
- **Fix:**
  1. In a terminal: `npx -y @neondatabase/mcp-server-neon --version` (or run it and see if it starts).
  2. Ensure Cursor is using a Node version that has `npx` (e.g. Node 18+).
  3. If you use a custom Node path, the MCP “command” in Cursor may need the same environment (e.g. same `PATH`) so that `npx` resolves correctly.

---

## 3. Quick verification

1. **API key:** You have a key at [Neon API Keys](https://console.neon.tech/app/settings/api-keys) and it’s set in Cursor MCP as `NEON_API_KEY`.
2. **Config:** Neon MCP type is **command**, command is **npx**, args include **-y** and **@neondatabase/mcp-server-neon**.
3. **Cursor:** Restart Cursor (or toggle the Neon MCP off/on) after changing config.
4. **Usage:** When asking the AI to run SQL, name your **Neon project** (and branch if you have more than one).

---

## 4. If you still see an error

Share the **exact error message** (and, if possible, the action you were doing, e.g. “Run SQL on project X”). Then we can target that specific failure (e.g. 404, auth, or timeout).

**Optional:** Run this in a terminal to confirm the MCP package runs and can use your key:

```bash
NEON_API_KEY="your-key-here" npx -y @neondatabase/mcp-server-neon
```

(Ctrl+C to stop.) If this fails, the problem is environment/Node/network or the key; if it runs, the issue is likely Cursor’s MCP config or how the AI is calling the tools.)

---

## 5. Using the database without the MCP

Your project already talks to Neon **without** the MCP:

- **Connection:** `.env` → `DATABASE_URL` (Neon connection string).
- **Create/update views:** `npm run db:views`
- **Refresh materialized views:** `npm run db:refresh-views`
- **Ingestion:** `python backend/python_scripts/ingest_to_postgres.py` (and it refreshes views at the end)

So even if the Neon MCP is broken, you can still manage and query the database with these commands and your usual SQL client or Tableau.
