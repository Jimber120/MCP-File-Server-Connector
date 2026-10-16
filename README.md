# Sandboxed Model Context Protocol (MCP) File-Server Connector

## 1. Project Overview
This repository provides a sandboxed Model Context Protocol (MCP) file-server connector designed for secure, autonomous AI agent interactions with a host computational environment. It implements an isolated file management runtime running Python MCP 2.x and containerized through Docker Compose with automated restart policies. The server exposes persistent Streamable HTTP endpoints via an ngrok static tunnel, enabling multi-session agent collaboration through shared workspace logs.

---

## 2. Technical Stack & Implementation Details

| Layer | Selected Implementation | Technical Description |
| :--- | :--- | :--- |
| **Runtime & SDK** | **Python 3.11+ & MCP 2.x (`mcp>=2`)** | Implements declarative `@mcp.tool()` handlers using `MCPServer` with native Python typing and asyncio support. |
| **Validation Layer** | **Pydantic v2 (`Field`)** | Handles parameter parsing and defines strict input contracts for all exposed MCP tools. |
| **Transport** | **Streamable HTTP / SSE (`/mcp`)** | Exposes an HTTP/SSE server running on port 8000 for remote agent tool execution. |
| **Exposure / Tunnel** | **ngrok Permanent Static Domain** | Routes inbound web traffic to the local Docker container using a dedicated static domain URL. |
| **Process Supervision** | **Docker Compose (`unless-stopped`)** | Manages server and tunnel lifecycles in the background across host reboots. |
| **Version Control** | **Containerized Git Subprocess** | Executes Git CLI commands directly within the sandboxed workspace to track project changes. |
| **Client Interface** | **Claude Client & MCP Bridge** | Connects to web agents via the static ngrok endpoint or desktop agents via an MCP bridge. |

---

## 3. MCP Tools Reference

| # | Tool Name | Parameters | Description |
| :-: | :--- | :--- | :--- |
| **1** | `list_files` | *None* | Lists all relative file paths inside the workspace, excluding `.git` directories. |
| **2** | `read_file` | `path: str` | Reads and returns the UTF-8 text contents of a file inside the workspace. |
| **3** | `write_file` | `path: str`, `content: str` | Creates or overwrites a file with text inside the workspace. |
| **4** | `str_replace` | `path: str`, `old_str: str`, `new_str: str` | Replaces a single unique occurrence of text within a file. |
| **5** | `delete_file` | `path: str` | Deletes a specified file inside the workspace. |
| **6** | `search_code` | `keyword: str` | Searches for text occurrences across files in the workspace. |
| **7** | `git_status` | *None* | Checks the working tree status of the workspace repository. |
| **8** | `git_commit` | `message: str` | Stages all workspace modifications and creates a commit with a message. |

---

## 4. Setup Guide

### Step 1: Install Dependencies
1. **Docker Desktop**:
   * Download and install from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/).
   * Ensure hardware virtualization is enabled in Task Manager and select the WSL 2 backend during installation.
2. **Git**:
   * Download and install from [git-scm.com](https://git-scm.com/).
3. **ngrok**:
   * Create a free account at [dashboard.ngrok.com](https://dashboard.ngrok.com/).
   * Claim a permanent static domain under **Universal Gateway > Domains** (e.g., `your-domain.ngrok-free.app`).
   * Retrieve your Auth Token from **Getting Started > Your Authtoken**.

### Step 2: Initialize Directory & Workspace
Open your terminal or command prompt, navigate to your desired directory, and set up the project folder structure:

```bash
mkdir "Python MCP"
cd "Python MCP"

# Create the workspace directory and initialize Git tracking
mkdir workspace
cd workspace
git init
type nul > PROJECT_STATE.md
type nul > PLAN_LOG.md
type nul > TRANSCRIPT.md
type nul > CHECKPOINTS.md
type nul > DECISIONS.md
git add .
git commit -m "Initialize handoff protocol ledgers"
cd ..
```
*(On Linux/macOS, use `touch` instead of `type nul >`)*.

### Step 3: Create Server and Container Configuration Files
In the root `Python MCP` folder, create the following core files:

* **`requirements.txt`**:
  ```text
  mcp>=2
  pydantic
  fastapi
  uvicorn
  ```

* **`Dockerfile`**:
  ```dockerfile
  FROM python:3.11-slim
  RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY server.py .
  EXPOSE 8000
  CMD ["python", "server.py"]
  ```

* **`docker-compose.yml`**:
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
  *(Replace `YOUR-STATIC-DOMAIN.ngrok-free.app` with your static ngrok domain, and insert your ngrok authtoken)*.

### Step 4: Launch the Containers
```bash
docker compose up -d --build
```
Verify container status:
```bash
docker compose ps
docker compose logs --tail=20 ngrok
```

---

## 5. Client Connection Setup

### Claude Web (Recommended)
1. Open Claude Web (`claude.ai`).
2. Go to **Settings > Connectors & Integrations**.
3. Add a Custom Connector:
   * **Connector URL**: `https://YOUR-STATIC-DOMAIN.ngrok-free.app/mcp`
   * **Authentication**: None.
4. Confirm that the connector displays an active green status.

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

## 6. Multi-Agent Protocol & Verification

The repository coordinates independent agent sessions with zero shared conversation memory by exchanging state through structured markdown files inside `workspace/`:

* **`PROJECT_STATE.md`**: Tracks active files, installed dependencies, and completed features.
* **`PLAN_LOG.md`**: Outlines the task queue and target deliverables for subsequent agent sessions.
* **`TRANSCRIPT.md`**: Chronological record of tool invocations, inputs, and architectural updates.
* **`CHECKPOINTS.md` & `DECISIONS.md`**: Notes architectural choices and milestones.

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
1. **Session 1 (Agent A)**: Scaffolds workspace, creates `index.html`, initializes markdown ledgers, commits to Git.
2. **Session 2 (Agent B)**: Reads state, implements `app.js` with dynamic DOM population, links script in `index.html` via `str_replace`, commits.
3. **Session 3 (Agent A)**: Performs `search_code('items')`, adds interactive click-to-strike handler, updates ledgers, commits.
4. **Session 4 (Agent B)**: Generates initial documentation, verifies complete project state, commits.
5. **Session 5 (Agent A)**: Milestone transition and scope expansion setup.
6. **Session 6 (Agent A)**: Implements 100 Random Grocery Items dataset generator in `app.js` across 7 categories, commits.
7. **Session 7 (Agent B)**: Creates `style.css` with responsive card grid and badges, links in `index.html`, commits.
8. **Session 8 (Agent A)**: Implements live search bar and category dropdown filter toolbar in `index.html` & `app.js`, commits.
9. **Session 9 (Agent B)**: Polishes UI, adds dynamic cart summary metrics, finalizes documentation and transcript audit, commits.

---

## 7. Troubleshooting & FAQ

* **Issue: `docker compose ps` fails with named pipe error (`pipe/dockerDesktopLinuxEngine`)**:
  * *Fix*: Launch Docker Desktop and wait 30–60 seconds until the engine icon in the lower-left turns green.
* **Issue: Claude Web reports `404 / Sign-in required`**:
  * *Fix*: Verify the URL ends with `/mcp` (e.g., `https://your-domain.ngrok-free.app/mcp`), and ensure `--request-header-add "ngrok-skip-browser-warning: true"` is included in `docker-compose.yml`.
* **Issue: `str_replace` fails with ambiguous matches error**:
  * *Fix*: Provide a larger snippet of surrounding text in `old_str` so that the match is strictly unique within the file.
