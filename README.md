# Salesforce write-spec skill

> [!WARNING]
> **Unofficial. This is not an official Salesforce skill** and is not supported by Salesforce. Use it at your own discretion.
>
> For org discovery, the skill uses **Agentforce Coworker over MCP** (the `AskCoworker` MCP server). The preferred approach will be the **metadata grounding MCP server launching in the October release**. Until that is available, you can use this skill.

An [Agent Skill](https://agentskills.io) that turns a plain-English Salesforce business requirement into a reviewable **implementation specification**, grounded in a real org. It works in **Claude Code**, the **Code tab of Claude Desktop**, and **Codex**. The repo also contains the eval harness used to build and harden the skill over 38 revisions.

The skill only writes specs. It never deploys, retrieves, changes metadata or data, or runs Apex. For discovery it uses Agentforce Coworker through the **AskCoworker** Salesforce hosted MCP server, and it checks every claim it relies on with read-only `sf` CLI queries.

```
/write-spec Flag accounts whose SLA expires in the next 30 days so account managers can renew. org: MyDevOrg
```

The spec is saved as plain Markdown to `design/<slug>-spec.md` in your working directory. An example is in [`design/review-aggregation-storefront-spec.md`](design/review-aggregation-storefront-spec.md).

---

## Quick start

1. **Org setup, once per org:** [register the AskCoworker MCP server](#2-register-the-askcoworker-mcp-server) and [create an External Client App](#3-create-an-external-client-app).
2. **Install the skill** in your agent (below).
3. **Connect AskCoworker** in your agent ([step 4](#4-connect-askcoworker-in-your-agent)).
4. Run it: `/write-spec <requirement> org: <alias>` (the invocation differs by agent; see the table).

## Install

| Agent | Install | Invoke |
| --- | --- | --- |
| **Claude Code** (plugin) | `claude plugin marketplace add msrivastav13/salesforce-write-spec-skill`<br>`claude plugin install salesforce-write-spec@salesforce-write-spec` | `/salesforce-write-spec:write-spec …` |
| **Claude Code** (plain skill) | `npx skills add msrivastav13/salesforce-write-spec-skill --skill write-spec -a claude-code -g` | `/write-spec …` |
| **Claude Desktop** | Use the **Code** tab, which runs Claude Code on your machine, and install with either Claude Code option above | as in Claude Code |
| **Codex** | `npx skills add msrivastav13/salesforce-write-spec-skill --skill write-spec -a codex -g` | `$write-spec …` |

To install from a local clone instead, pass its path, e.g. `claude plugin marketplace add ~/src/salesforce-write-spec-skill`. Inside Claude Code the interactive equivalents are `/plugin marketplace add …` and `/plugin install …`.

**Without `npx`:** copy the skill folder yourself.

```bash
# Claude Code
mkdir -p ~/.claude/skills && cp -R skills/write-spec ~/.claude/skills/
# Codex
mkdir -p ~/.agents/skills && cp -R skills/write-spec ~/.agents/skills/
```

**Developing the skill in this repo:** run `claude --plugin-dir .` to load it for one session without installing it (`/reload-plugins` picks up edits).

Notes:
- **Explicit invocation only.** The skill doesn't trigger on its own: `disable-model-invocation: true` in Claude Code, and `allow_implicit_invocation: false` in `skills/write-spec/agents/openai.yaml` for Codex.
- **Claude Desktop Chat and Cowork aren't supported.** The skill has to run `sf` against an org you're logged in to on your own machine, so use the Code tab.
- **Cross-agent installer.** The `npx skills` commands come from [vercel-labs/skills](https://github.com/vercel-labs/skills). The Claude Code plugin install was tested end to end; the `npx` path was not.

---

## Prerequisites

### 1. Tools and an authorized org

- An agent from the table above
- [Salesforce CLI](https://developer.salesforce.com/tools/salesforcecli) (`sf`), logged in to a Developer Edition org or a sandbox:

  ```bash
  sf org login web --alias MyDevOrg
  ```

Name the org by adding `org: <alias>` to the skill's arguments. Without it, the skill uses your CLI default (`sf config get target-org`) and names that org in Section 2 of the spec. The skill needs no Python or other runtime; Python 3 is only for the optional eval aggregator.

### 2. Register the AskCoworker MCP server

In **Setup → MCP Servers**, create a **Custom** MCP server:

| Field | Value |
| --- | --- |
| API Name | `AskCoworker` |
| Tool | `SearchAgent_1` (source: **Agentforce Agents**), the agent that runs multi-step retrieval over org and enterprise sources |
| Status | **Active** |
| Server URL (generated) | `https://api.salesforce.com/platform/mcp/v1/custom/AskCoworker` |

![AskCoworker MCP server details](docs/images/01-mcp-server-details.png)
![AskCoworker MCP server tool](docs/images/02-mcp-server-tools.png)

The API name must be exactly `AskCoworker`, and you must register it in your agent under the same name (step 4). In Claude Code the skill calls the tool as `mcp__AskCoworker__SearchAgent_1`.

### 3. Create an External Client App

In **Setup → External Client App Manager**, create an External Client App with OAuth enabled:

- **Callback URLs** (one per line):
  - Claude Code: `http://localhost:38000/callback`
  - Codex: the exact URL that `codex mcp add` prints (step 4)
- **Selected OAuth scopes:**
  - `Perform requests at any time (refresh_token, offline_access)`
  - `Access Salesforce hosted MCP servers (mcp_api)`
- **Security:** leave **Require secret for Web Server Flow** and **Require secret for Refresh Token Flow** unchecked. The agents are public clients that use PKCE, which is required and on by default. Refresh-token rotation and JWT-based access tokens are also on.

![External Client App OAuth settings](docs/images/03-eca-oauth-settings.png)
![External Client App security settings](docs/images/04-eca-security-settings.png)

After saving, open **Consumer Key and Secret** and copy the **Consumer Key**. It is the OAuth client ID in step 4. Don't commit it.

### 4. Connect AskCoworker in your agent

The MCP server can't be bundled with the plugin, because each org's External Client App has its own consumer key. Register it once per machine.

**Claude Code** (CLI or the Desktop Code tab). This follows Philippe Ozil's Salesforce Developers blog post on connecting Claude Code to Salesforce hosted MCP servers:

```bash
claude mcp add --transport http --scope user \
  --client-id <CONSUMER_KEY> \
  --callback-port 38000 \
  AskCoworker https://api.salesforce.com/platform/mcp/v1/custom/AskCoworker
```

`--scope user` makes the server available in every directory. Leave it out to register it for the current directory only. Then run `/mcp`, choose **AskCoworker → Authenticate**, and log in to the org in the browser.

**Codex:**

```bash
codex mcp add AskCoworker --url https://api.salesforce.com/platform/mcp/v1/custom/AskCoworker --oauth-client-id <CONSUMER_KEY>
codex mcp login AskCoworker
```

`codex mcp add` prints an `OAuth callback URL`. Add that exact URL to the External Client App's callback URLs before you run `codex mcp login`.

---

## Using the skill

```
/write-spec <business requirement> [org: <alias>]
```

What the skill does, in order (full detail in [`SKILL.md`](skills/write-spec/SKILL.md)):

1. **Context.** Resolves the target org and checks that it is reachable. It never prints the access token. When run inside an SFDX project, it also reads `sourceApiVersion`.
2. **Discover.** Sends narrow, word-limited AskCoworker calls for objects and behavior.
3. **Verify.** Runs read-only `sf sobject describe` / `sf data query` checks on every claim the design depends on.
4. **Scope.** Asks you up to 3 intent questions (business values, persona, ambiguous deletes). It decides implementation details itself.
5. **Inventory, runtime, and security details.** More AskCoworker calls, each checked against the org.
6. **Render, self-check, save.** Checks the format rules before saving to `design/<slug>-spec.md`: the nine sections, matching change lists in Sections 4 and 9, and a counts line that matches the table. It never overwrites a completed spec with a worse one.

Every fact in the spec is tagged *verified by org query*, *verified by project file*, *reported by AskCoworker*, *user decision*, or *assumption*.

---

## Repository layout

```
.claude-plugin/               # Claude Code plugin + marketplace manifests (the repo is both)
skills/write-spec/            # the skill (the only copy; every install method uses it)
  SKILL.md
  reference/                  # AskCoworker call templates, design rules, org-verification queries, scope rules, spec format
  agents/openai.yaml          # Codex metadata (explicit invocation only)
design/                       # specs written by the skill
evals/write-spec/
  requirements.jsonl          # 120 eval requirements (id, category, requirement, hidden intent, expectations)
  meta/<id>.json              # per-case expectations used by the judge
  RUNNER.md                   # protocol for an agent running one eval case with a simulated user
  JUDGE.md                    # protocol for an independent judge that spot-checks claims against the org
  aggregate.py                # merges run/judge results and checks trust gates
  CHANGELOG.md                # every skill revision, with the eval evidence behind it
  SKILL_REV                   # current skill revision
  skill-versions/vN/          # snapshot of the skill at each revision
  runs/{pilot,main,regress,regress2,final}/<id>/   # case.json, intent.json, run.json, judge.json, saved spec
docs/images/                  # setup screenshots
LICENSE                       # Apache 2.0
```

---

## Running the evals

Each case directory holds `case.json` (id and requirement) and `intent.json` (the simulated user's hidden intent). The runner and judge pin the org alias `TestWriteSpecDE`, because the expectations in `meta/*.json` describe that org's data. If you use a different alias, change it in `RUNNER.md` and `JUDGE.md`.

1. **Run a case.** Start a Claude Code agent with `RUNNER.md` as its instructions and `out=evals/write-spec/runs/<batch>/<id>`. The agent runs the skill, answers its own questions from `intent.json`, saves the spec under `out`, and writes `run.json`.
2. **Judge it.** A separate agent follows `JUDGE.md`. It checks up to 6 claims against the org, looks for duplicate Creates and phantom Update/Delete targets, scores six dimensions from 0 to 2, and writes `judge.json`.
3. **Aggregate:**

   ```bash
   python3 evals/write-spec/aggregate.py evals/write-spec/runs/main [evals/write-spec/runs/final ...]
   ```

### Current results (`runs/main`, 118 cases, 105 judged)

| Gate | Result |
| --- | --- |
| Safety violations | 0 ✅ |
| Claim accuracy | 96.9% (592 correct / 19 wrong / 10 unverifiable) ✅ |
| Duplicate Creates or phantom targets | 1 ❌ |
| Ask-user agreement with generator labels | 60.4% ❌ (informational; labels were written without seeing the org) |
| Implementation questions per judged run | 0.16 ✅ |
| Missing intent questions | 4 ❌ |
| Mean requirement fit / honesty (0–2) | 1.83 / 1.83 ✅ |

These results are from v1–v35, which still used the Python validator. It was removed in v38: in 124 runs it caught only 3 format issues, none after v23, and every material defect above came from the judge. Many of the failures come from early revisions. See `CHANGELOG.md` for what each revision fixed, and the `regress*` and `final` batches for reruns on later revisions.
