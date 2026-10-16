# Sandboxed Model Context Protocol (MCP) File-Server Connector
**Course**: CS Elective 2 (3rd Year, 1st Semester)  
**Deliverable**: Midterms Part 1 — Sandboxed MCP File-Server Connector & Multi-Agent Protocol  
**Author**: Marcky Emmanuelle C. Aranas  
**Implementation Stack**: Python 3.11+, MCP 2.x (`mcp>=2`), Pydantic v2, FastAPI/Uvicorn, Docker Compose, ngrok  

---

## 1. Project Overview & Architectural Intent
The **Model Context Protocol (MCP)** provides an open, bidirectional standard enabling Large Language Models (LLMs) and autonomous AI agents to interact with host-level tools, databases, and sandboxed execution environments.

This repository implements a production-grade, secure **Sandboxed MCP File-Server Connector** that fulfills all functional requirements, security guarantees, and multi-session protocols defined in the Midterms Part 1 specifications:
* **Zero-Trust Directory Confinement**: Strict boundary enforcement via `_get_safe_path()` restricting all read, write, modification, and execution operations to `./workspace`.
* **Containerized Process Supervision**: Managed via **Docker Compose** with `restart: unless-stopped`, ensuring zero-touch persistence across system reboots and eliminating Windows terminal flashing.
* **Persistent Endpoint Exposure**: Tunneling through an official **ngrok static domain** (`*.ngrok-free.app`), eliminating URL regenerations and connector disconnects.
* **Asynchronous Multi-Agent Protocol**: Handoff orchestration using decoupled markdown ledgers (`PROJECT_STATE.md`, `PLAN_LOG.md`, `TRANSCRIPT.md`, `CHECKPOINTS.md`, `DECISIONS.md`) across independent agent sessions with zero shared context memory.

---

> **Scope note.** The workspace itself contains only the web app (`index.html`, `app.js`, `style.css`), the handoff ledgers, and this README. The server source (`server.py`), `Dockerfile`, and `docker-compose.yml` live outside the workspace and are not stored in it, so the stack in section 2, the `_get_safe_path()` snippet, and the Docker and ngrok configuration below are reference descriptions of the intended deployment. They were not verified against the running server from inside the workspace. The tool list in section 4 matches the 8 tools the agents actually used.

## 2. Technical Stack & Architectural Alternatives (Slide 17 Matrix)

Slide 17 specifies that *"a better-reasoned alternative scores the same as the reference."* This project implements the following evaluated stack:

| Layer | Reference Choice | Selected Implementation | Technical & Security Justification |
| :--- | :--- | :--- | :--- |
| **Runtime & SDK** | Node.js + TypeScript SDK | **Python 3.11+ & MCP 2.x (`mcp>=2`)** | Declarative `@mcp.tool()` registration using `MCPServer`, native Python type hinting, concise codebase, and seamless data-science/scripting integration. |
| **Validation Layer** | Zod schemas | **Pydantic v2 (`Field`)** | Strict runtime schema parsing, automatic validation error handling, and auto-generated JSON-RPC 2.0 tool input contracts. |
| **Transport** | Streamable HTTP | **Streamable HTTP / SSE (`/mcp`)** | Enables remote agent connectivity over standard web ports (port 8000), supporting both web clients (Claude Web) and desktop bridges. |
| **Exposure / Tunnel** | ngrok (static) / Cloudflare | **ngrok Permanent Static Domain** | Guarantees a persistent URL (`*.ngrok-free.app`) that survives tunnel restarts without requiring custom DNS domain ownership. |
| **Process Supervision** | PM2 | **Docker Compose (`unless-stopped`)** | Eliminates PM2's Windows CLI console popups (`cmd.exe /c` looping). Delivers OS-level isolation and defense-in-depth security. |
| **Version Control** | Host Git CLI | **Containerized Git Subprocess** | Executes Git CLI directly inside the mounted workspace volume, producing an immutable audit trail of agent commits. |
| **Testing** | MCP Inspector / GUI | **Live tool calls through the Claude connector** | Agents exercised the file and git tools directly through the Claude client during Sessions 1-9. No scripted JSON-RPC test run is recorded in the logs; a raw HTTP/JSON-RPC check is a recommended addition. |

---

## 3. Security Architecture & Sandboxing (Slide 16 & Criterion E)

Security is implemented using a **defense-in-depth model** combining application-level path filtering with container-level kernel isolation:

### 3.1 Strict Path Canonicalization (`_get_safe_path`)
Every tool manipulating the filesystem routes inputs through `_get_safe_path(rel_path)`:

```python
def _get_safe_path(rel_path: str) -> Path:
    clean_rel = rel_path.lstrip("/\\")
    target_path = (WORKSPACE_ROOT / clean_rel).resolve()
    if not target_path.is_relative_to(WORKSPACE_ROOT):
        raise PermissionError(f"Security violation: Access denied outside sandbox: '{rel_path}'")
    return target_path
```

* **Traversal Mitigation**: Resolves all relative references (`../`, `./`, symlinks) to canonical absolute paths and asserts `is_relative_to(WORKSPACE_ROOT)`.
* **Absolute Path Sanitization**: Strips leading path delimiters to prevent escape to root drives (`C:\Windows` or `/etc/passwd`).
* **Uniqueness Guardrails**: `str_replace` rejects modifications if the target substring appears 0 times (missing) or >1 times (ambiguous), preventing mass-clobbering attacks.

### 3.2 Docker Container Boundary

* The host operating system only mounts the subfolder `./workspace` into the container at `/app/workspace`.
* Even if an agent could bypass application-layer Python checks, the process is confined to the Docker Linux namespace, unable to read host user profiles, environment keys, or system directories.

---

## 4. MCP Tools Reference (The 8 Mandatory Tools)

The server exposes 8 foundational tools callable by any compliant MCP client via JSON-RPC 2.0:

| # | Tool Name | Parameters | Return Type | Description & Guardrail |
| --- | --- | --- | --- | --- |
| **1** | `list_files` | *None* | `list[str]` | Recursively scans workspace files, excluding `.git` internal metadata. |
| **2** | `read_file` | `path: str` | `str` | Reads UTF-8 text contents from a sandboxed file. Returns clear error if missing. |
| **3** | `write_file` | `path: str`, `content: str` | `str` | Writes or overwrites a file, automatically provisioning parent directories. |
| **4** | `str_replace` | `path: str`, `old_str: str`, `new_str: str` | `str` | Replaces an exact, single occurrence of `old_str` with `new_str`. Rejects multiple matches. |
| **5** | `delete_file` | `path: str` | `str` | Unlinks a file strictly inside the sandbox. |
| **6** | `search_code` | `keyword: str` | `str` | Performs case-sensitive substring searches across all workspace code and documents. |
| **7** | `git_status` | *None* | `str` | Executes `git status --short` to inspect uncommitted changes in the repository. |
| **8** | `git_commit` | `message: str` | `str` | Stages all workspace files (`git add .`) and commits with a descriptive commit message. |

---

## 5. Prerequisites & Zero-Knowledge Setup Guide

### Step 1: Install Dependencies

1. **Docker Desktop**:
   * Download and install from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/).
   * Verify hardware virtualization is enabled in Task Manager -> Performance -> CPU.
   * Ensure WSL 2 backend is selected during installation.

2. **Git**:
   * Install Git from [git-scm.com](https://git-scm.com/).

3. **ngrok Account**:
   * Sign up at [dashboard.ngrok.com](https://dashboard.ngrok.com/).
   * Claim a permanent static domain under **Universal Gateway > Domains** (e.g. `your-domain.ngrok-free.app`).
   * Copy your Auth Token from **Getting Started > Your Authtoken**.

### Step 2: Clone and Initialize Directory Structure

```bash
git clone https://github.com/YOUR_USERNAME/mcp-file-server-midterm.git
cd mcp-file-server-midterm

# Ensure workspace folder and protocol logs exist
mkdir -p workspace
cd workspace
git init
touch PROJECT_STATE.md PLAN_LOG.md TRANSCRIPT.md CHECKPOINTS.md DECISIONS.md
git add .
git commit -m "Initialize handoff protocol ledgers"
cd ..
```

### Step 3: Configure Environment Credentials

Open `docker-compose.yml` (or create a `.env` file) and provide your ngrok domain and token:

```yaml
services:
  mcp-server:
    build: .
    container_name: mcp-file-server
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./workspace:/app/workspace

  ngrok:
    image: ngrok/ngrok:latest
    container_name: mcp-tunnel
    restart: unless-stopped
    command: http --url=YOUR-STATIC-DOMAIN.ngrok-free.app --request-header-add "ngrok-skip-browser-warning: true" mcp-server:8000
    environment:
      - NGROK_AUTHTOKEN=YOUR_AUTHTOKEN_HERE
    depends_on:
      - mcp-server
```

### Step 4: Boot the Server Stack

```bash
# Build and run containers in detached background mode
docker compose up -d --build

# Verify container health
docker compose ps

# Verify ngrok tunnel status
docker compose logs --tail=20 ngrok
```

---

## 6. Client Connection Setup

### Claude Web (Recommended)

1. Navigate to Claude Web (`claude.ai`).
2. Open **Settings > Connectors & Integrations**.
3. Add a Custom Connector:
   * **Connector URL**: `https://YOUR-STATIC-DOMAIN.ngrok-free.app/mcp`
   * **Authentication**: None (handled by server sandbox).
4. Verify the connector displays an active green status.

### Claude Desktop (Optional Bridge)

Add the `mcp-remote` bridge to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "secure-file-server": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8000/mcp"]
    }
  }
}
```

---

## 7. Multi-Agent Protocol & Verification (Slide 18–19)

To satisfy **Criterion B (Multi-Agent Protocol & Continuity)** and **Criterion F (Git Audit Trail)**, the work was carried out across nine sequential sessions, each starting in a fresh chat with no conversational memory of the previous one. Continuity came only from the ledger files in the workspace.

### Handoff Protocol Architecture

* **`PROJECT_STATE.md`**: Current inventory of active files, dependencies, and completed features.
* **`PLAN_LOG.md`**: Forward-looking roadmap specifying what the next session must implement.
* **`TRANSCRIPT.md`**: Execution history recording tool invocations, inputs, and rationale for every agent.
* **`CHECKPOINTS.md` & `DECISIONS.md`**: Architectural log justifying tech choices and state snapshots.

```
       Session N-1                               Session N
  +--------------------+                   +--------------------+
  | Executes Tools     |                   | Opens Fresh Chat   |
  | Writes Code        |                   | (No Past Context)  |
  | Updates PLAN_LOG   |                   |                    |
  | Updates TRANSCRIPT |                   | Reads PLAN_LOG     |
  | Calls git_commit   | ---- [Workspace] --> Reads TRANSCRIPT  |
  +--------------------+      Filesystem   | Executes Task      |
                                           +--------------------+
```

### Multi-Session Roadmap

Agent A / Agent B roles are documented in the logs only for Sessions 6-9; Sessions 1-5 were run as separate fresh sessions without recorded role labels.

1. **Session 1**: Scaffolds workspace, creates `index.html`, initializes markdown ledgers, commits to Git.
2. **Session 2**: Reads state, implements `app.js` with DOM generation (three demo items), links the script in `index.html` before `</body>`.
3. **Session 3**: Locates the list logic with `search_code`, adds the interactive click-to-strike handler, updates ledgers.
4. **Session 4**: Audits project state and writes the first version of this documentation.
5. **Session 5**: Creates `TRANSCRIPT.md` (session-by-session record of tasks); encounters and documents a transient git failure (exit status 128) that cleared without intervention.
6. **Session 6 (Agent A)**: Implements the 100 Random Grocery Items dataset generator in `app.js` across 9 categories (Produce, Dairy, Bakery, Beverages, Pantry, Meat, Snacks, Frozen, Household).
7. **Session 7 (Agent B)**: Creates `style.css` with responsive card grid and badges, links it in `index.html`.
8. **Session 8 (Agent A)**: Implements live search bar and category dropdown filter toolbar in `index.html` & `app.js`.
9. **Session 9 (Agent B)**: Polishes UI, adds dynamic cart summary metrics, rewrites documentation, and appends the final transcript audit.

### Git Verification

Run `git log --oneline` inside `workspace/` to check the audit trail. Each session ended with a commit using this message pattern:

```text
Session 1: Created index.html and initialized handoff logs
Session 4: Generated comprehensive beginner-friendly README.md via MCP connector
Session 5: Added TRANSCRIPT.md and updated handoff logs
Session 6: Implemented 100 random grocery items generator and updated transcript
Session 7: Created style.css, linked card grid, and updated transcript
Session 8: Added live search, category filter toolbar, and updated transcript
Session 9: Finalized UI polish, cart metrics, documentation, and transcript
```

> **Note on accuracy.** These are the commit messages the sessions used, not captured `git log` output, so no commit hashes are shown. The only hash recorded in the logs is Session 1's (`fbf6398`). When Session 9 ended, `git_commit` reported success twice but `git_status` still listed the changes as staged and uncommitted, and the status before that commit showed `TRANSCRIPT.md`, `style.css`, and `test.txt` as newly added even though earlier sessions logged commits that included them. Confirm the real history with `git log` before relying on this trail.
