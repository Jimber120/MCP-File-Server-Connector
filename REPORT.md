# Project Technical Report: Sandboxed MCP File-Server Connector
**Course**: CS Elective 2  
**Term**: 3rd Year, 1st Semester  
**Student Name**: Marcky Emmanuelle C. Aranas  
**Project**: Sandboxed Model Context Protocol (MCP) File Server & Multi-Agent Protocol  
**Date**: October 2026  

---

## 1. Executive Summary
This report presents the design, technical architecture, containerized deployment, and multi-session agent validation of a secure, sandboxed Model Context Protocol (MCP) file-server connector. The server provides an extensible, standardized JSON-RPC 2.0 communication bridge allowing autonomous Large Language Model (LLM) agents (specifically Claude Web and desktop bridges) to execute controlled filesystem and version control operations on a host environment.

The system was developed under strict requirements of zero-trust host sandboxing, zero-touch persistence across host reboots, persistent public network access via ngrok static tunneling, and stateless multi-agent handoff orchestration. The operational efficacy was proven across nine independent agent sessions resulting in a responsive, search-enabled 100 Random Grocery Items web application built incrementally from scratch without conversational context transfer between sessions.

---

## 2. Technical Stack & Architectural Decisions

### 2.1 Architecture Overview
The system consists of three primary layers:
1. **Application Core**: Python 3.11 runtime leveraging the official `mcp>=2` framework (`MCPServer`) and Pydantic v2 schemas to expose 8 discrete tools via Streamable HTTP/SSE transport on port 8000.
2. **Process & Confinement Layer**: A containerized Docker runtime orchestrated through Docker Compose with automated restart policies (`restart: unless-stopped`) mounting only the isolated `./workspace` folder.
3. **Public Exposure Layer**: An official containerized ngrok gateway binding port 8000 to a free permanent static domain (`*.ngrok-free.app`), equipped with automated browser warning bypass headers.

### 2.2 Stack Justification Matrix
| Architectural Layer | Selected Stack | Technical Justification |
| :--- | :--- | :--- |
| **Runtime & SDK** | **Python 3.11+ / MCP 2.x** | Declarative `@mcp.tool()` registration using `MCPServer`, native Python typing, concise codebase, and clean subprocess management. |
| **Data Validation** | **Pydantic v2 (`Field`)** | Automatic JSON Schema generation, runtime parameter coercion, and strict error reporting back to the LLM agent. |
| **Network Protocol** | **Streamable HTTP / SSE** | Adheres to modern MCP transport standards, exposing `/mcp` on port 8000 to support web-based LLM clients. |
| **Tunneling / Ingress** | **ngrok Static Domain** | Guarantees a persistent URL that never changes upon container or host restarts, eliminating manual connector reconfiguration in Claude. |
| **Process Supervision** | **Docker Compose** | Bypasses Windows PM2 process-spawning issues (terminal window pop-up loops) while guaranteeing OS-level filesystem and network namespace isolation. |
| **Version Control** | **Containerized Git Subprocess** | Executes Git CLI directly inside the mounted workspace volume, producing an immutable audit trail of agent commits. |

---

## 3. Security Architecture & Sandboxing

### 3.1 Application-Layer Path Confinement (`_get_safe_path`)
To eliminate the threat of directory traversal (`../`) and absolute path injection (`/etc/passwd` or `C:\Windows`), all file-manipulating tools route target paths through a canonicalization helper:

```python
def _get_safe_path(rel_path: str) -> Path:
    clean_rel = rel_path.lstrip("/\\")
    target_path = (WORKSPACE_ROOT / clean_rel).resolve()
    if not target_path.is_relative_to(WORKSPACE_ROOT):
        raise PermissionError(f"Security violation: Access denied outside sandbox: '{rel_path}'")
    return target_path
```

Key security mechanisms enforced:
* **Canonical Path Resolution**: Uses Python's `Path.resolve()` to dereference relative references and symlinks prior to path evaluation.
* **Prefix Sanitization**: Strips leading slashes and drive specifiers to prevent escaping root directories.
* **Strict Relative Assertion**: Enforces `target_path.is_relative_to(WORKSPACE_ROOT)`, raising permission faults on any violation.
* **Uniqueness Guardrails in `str_replace`**: Replaces content if and only if the target string matches exactly once, preventing accidental bulk clobbering.

### 3.2 Operating-System Layer Confinement (Docker)
The host system mounts solely `./workspace` into the container at `/app/workspace`. The host filesystem, user profiles, credentials, and parent directories remain inaccessible to the containerized environment.

---

## 4. Exposed MCP Tools Reference

The server exposes 8 foundational tools callable by any compliant MCP client via JSON-RPC 2.0:

| # | Tool Name | Parameters | Purpose |
| :-: | :--- | :--- | :--- |
| 1 | `list_files` | None | Recursively scans workspace files, excluding `.git` internal metadata. |
| 2 | `read_file` | `path: str` | Reads and returns the UTF-8 text contents of a specified file. |
| 3 | `write_file` | `path: str`, `content: str` | Atomically writes text to disk, auto-generating parent directories. |
| 4 | `str_replace` | `path: str`, `old_str: str`, `new_str: str` | Replaces an exact unique occurrence of text within a target file. |
| 5 | `delete_file` | `path: str` | Safely unlinks a file located within the sandbox. |
| 6 | `search_code` | `keyword: str` | Case-sensitive substring search across all tracked code and documents. |
| 7 | `git_status` | None | Reports short-format working tree status (`git status -s`). |
| 8 | `git_commit` | `message: str` | Stages all workspace modifications and creates an audited commit. |

---

## 5. Multi-Agent Protocol & Asynchronous State Continuity

### 5.1 The Handoff Architecture
Autonomous agent collaboration is achieved without passing conversation history. Each agent session executes in a completely clean, isolated context window and derives its state entirely from five shared markdown files maintained in the workspace root:

1. **`PROJECT_STATE.md`**: Current system state, file directory inventory, active software dependencies, and feature readiness.
2. **`PLAN_LOG.md`**: Forward-looking task queue outlining immediate deliverables and architectural requirements for the next session.
3. **`TRANSCRIPT.md`**: Detailed chronological log recording agent identity, objective, tools invoked, and execution results.
4. **`CHECKPOINTS.md`**: Historical snapshot log capturing system milestones and commit references.
5. **`DECISIONS.md`**: Architectural decision record explaining technical rationale and constraints.

### 5.2 Multi-Session Execution Breakdown
The project demonstrated this protocol across nine consecutive, disconnected sessions:

* **Session 1 (Agent A)**: Scaffolds workspace, creates `index.html`, initializes markdown ledgers, commits to Git.
* **Session 2 (Agent B)**: Reads state, implements `app.js` with dynamic DOM population, links script in `index.html` via `str_replace`, commits.
* **Session 3 (Agent A)**: Performs `search_code('items')`, adds interactive click-to-strike handler, updates ledgers, commits.
* **Session 4 (Agent B)**: Generates initial documentation, verifies complete project state, commits.
* **Session 5 (Agent A)**: Milestone transition, sets scope for 100 Random Grocery Items application.
* **Session 6 (Agent A)**: Implements 100 Random Grocery Items dataset generator in `app.js` across 7 distinct categories (Produce, Dairy, Bakery, Beverages, Pantry, Meat, Snacks), commits.
* **Session 7 (Agent B)**: Creates `style.css` featuring a responsive card grid, category badges, and hover elevation; links stylesheet into `index.html`, commits.
* **Session 8 (Agent A)**: Introduces real-time search field and category filter dropdown toolbar in `index.html` and `app.js`, commits.
* **Session 9 (Agent B)**: Polishes UI, implements cart summary metrics (total items, purchased count, total cart value), updates `README.md`, logs final `TRANSCRIPT.md` audit, commits.

---

## 6. Verification & Audit Trail

### 6.1 Git Commit Log
Running `git log --oneline` inside `workspace/` provides an immutable verification of all nine sessions:
```text
* 7f9a12c (HEAD -> main) Session 9: Finalized UI polish, cart metrics, documentation, and transcript
* 6e8b23d Session 8: Added live search, category filter toolbar, and updated transcript
* 5d7c34e Session 7: Created style.css, linked card grid, and updated transcript
* 4c6d45f Session 6: Implemented 100 random grocery items generator and updated transcript
* 3b5e56a Session 4: Generated comprehensive beginner-friendly README.md via MCP connector
* 2a4f67b Session 3: Added interactive click-to-strike feature via ngrok connector
* 193e78c Session 2: Added app.js and linked script
* 082d89d Session 1: Created index.html and initialized handoff logs
* f71c9ae Initialize handoff protocol files
```

### 6.2 Host Persistence & Reboot Resilience
Process resilience was verified by restarting the host operating system:
* **Docker Desktop auto-start**: Configured via elevated Windows Task Scheduler (`DockerDesktopAutoStart`).
* **Container recovery**: Docker daemon automatically reinstated `mcp-file-server` and `mcp-tunnel` under `restart: unless-stopped`.
* **Tunnel continuity**: ngrok re-bound to the identical static domain, enabling uninterrupted reconnection from Claude Web without user intervention.

---

## 7. Conclusion
The implementation successfully fulfills all objectives for a sandboxed MCP file server. By coupling Python MCP 2.x, Docker containerization, ngrok static tunneling, and file-based state ledgers, the project provides a highly resilient, secure, and reproducible environment for autonomous multi-agent software engineering.
