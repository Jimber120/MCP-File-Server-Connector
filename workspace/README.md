# MCP File-Server Connector

A small, self-contained project that lets an AI model (Claude) read, write, search, and version-control files in a **sandboxed folder on your own computer**, through the **Model Context Protocol (MCP)**.

This README is written so that someone with **zero technical background** can rebuild everything from scratch.

> **Honesty note on this document.** Sections marked **[Verified]** were checked against files in the workspace. Sections marked **[Reconstructed]** (the reference `server.py`, and the exact session prompts) were rebuilt by Session 4 because the original `server.py` is not stored inside the workspace and the original prompts were not logged. Test them before relying on them.

---

## Table of Contents

1. [What is this?](#1-what-is-this)
2. [Prerequisites (zero-knowledge guide)](#2-prerequisites-zero-knowledge-guide)
3. [Installation and setup](#3-installation-and-setup)
4. [Server architecture and tool reference](#4-server-architecture-and-tool-reference)
5. [Persistent public deployment](#5-persistent-public-deployment)
6. [Multi-session demonstration log](#6-multi-session-demonstration-log)
7. [What the demo project contains](#7-what-the-demo-project-contains)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. What is this?

### The problem
AI models like Claude live in the cloud. They cannot see the files on your computer, and they cannot run commands there.

### The solution: MCP
**Model Context Protocol (MCP)** is an open standard that defines how an AI model talks to external tools and data. Think of it as the **"USB-C for AI"**: just as one USB-C port lets many different devices connect to a laptop, MCP gives one standard plug that lets many tools connect to many AI apps.

### How this project fits together

```
 Claude (web/desktop)
        |
        |  HTTPS  (public URL from ngrok)
        v
   ngrok tunnel  ---->  server.py on your computer (port 8000)
                              |
                              v
                        workspace/  (sandboxed folder, a git repo)
```

- **`server.py`** is an MCP server exposing 8 file/git tools.
- **ngrok** gives your local server a public HTTPS address so Claude (in the cloud) can reach it.
- **`workspace/`** is the only folder the AI can touch. It is also a git repository, so every change can be committed and reversed.

---

## 2. Prerequisites (zero-knowledge guide)

You need four programs and one free account. Install in this order.

### 2.1 Python
- Download: https://www.python.org/downloads/
- Click the big yellow **Download Python** button and run the installer.

> ## WARNING (Windows)
> On the **first installer screen**, tick the box **"Add python.exe to PATH"** *before* clicking **Install Now**.
> If you skip this, the `python` and `pip` commands used below will not work, and you will need to uninstall and reinstall Python.

Verify: open a terminal (see 2.5) and run `python --version`. You should see a version number.

### 2.2 VS Code (text editor)
- Download: https://code.visualstudio.com/download
- Run the installer with default options.

### 2.3 Git (version control)
- Download: https://git-scm.com/downloads
- Run the installer with default options.

Verify: `git --version`

### 2.4 ngrok (public tunnel)
- Download: https://ngrok.com/download
- Windows: unzip and place `ngrok.exe` somewhere easy (e.g. `C:\ngrok`), or install via the Microsoft Store / `winget install ngrok.ngrok`.
- macOS: `brew install ngrok` (or use the download page).

#### Create an ngrok account and claim a free static domain
1. Go to https://dashboard.ngrok.com/signup and sign up (email or Google/GitHub).
2. Verify your email address.
3. In the dashboard, copy your **Authtoken** (https://dashboard.ngrok.com/get-started/your-authtoken).
4. Register the token on your computer:
   ```
   ngrok config add-authtoken YOUR_TOKEN_HERE
   ```
5. In the dashboard, open **Domains** (https://dashboard.ngrok.com/domains) and click **Create Domain** / **New Domain** to claim your **free static domain**. It looks like `something-random-words.ngrok-free.app` (some accounts get `.ngrok-free.dev`). **Write it down**; this is your `<domain>` below.

### 2.5 Opening a terminal
- **Windows:** press the Windows key, type `PowerShell`, press Enter. (Or open VS Code and press `` Ctrl+` ``.)
- **macOS:** press Cmd+Space, type `Terminal`, press Enter.

---

## 3. Installation and setup

Commands below are for **Windows PowerShell**. macOS/Linux differences are noted.

### 3.1 Create the folders
```powershell
mkdir mcp-file-server
cd mcp-file-server
mkdir workspace
```

### 3.2 Create and activate the Python virtual environment
A virtual environment keeps this project's libraries separate from the rest of your computer.

```powershell
python -m venv venv
```

Activate it:

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows Command Prompt
venv\Scripts\activate.bat

# macOS / Linux
source venv/bin/activate
```

When active, your prompt starts with `(venv)`.

> If PowerShell says scripts are disabled, run once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then try again.

### 3.3 Install required libraries
```powershell
pip install "mcp<2" pydantic fastapi uvicorn fastmcp
```

### 3.4 Initialize git inside `workspace/`
```powershell
cd workspace
git init
git config user.name "Your Name"
git config user.email "you@example.com"
cd ..
```

### 3.5 Create `server.py` **[Reconstructed]**
Open the project folder in VS Code (`code .`), create a file named `server.py` in the project root (next to `workspace/`), and paste the reference implementation from [section 4.3](#43-reference-serverpy-reconstructed).

---

## 4. Server architecture and tool reference

### 4.1 The 8 tools

| # | Tool | Purpose | Key arguments | Returns |
|---|------|---------|---------------|---------|
| 1 | `list_files` | List all non-hidden files tracked in the workspace | none | File names |
| 2 | `read_file` | Read a file's plain-text contents | `path` | File text |
| 3 | `write_file` | Create or overwrite a file | `path`, `content` | Confirmation |
| 4 | `str_replace` | Replace one **unique** exact snippet in a file | `path`, `old_str`, `new_str` | Confirmation, or an error if the snippet is missing or appears more than once |
| 5 | `delete_file` | Safely delete a file inside the sandbox | `path` | Confirmation |
| 6 | `search_code` | Search a keyword across all non-hidden files | `keyword` | Matching files/lines |
| 7 | `git_status` | Show the git working-tree status | none | `git status` output |
| 8 | `git_commit` | Stage all changes and create a commit | `message` | Commit result |

### 4.2 Security: the path-traversal sandbox, `_get_safe_path()`

**The risk.** If a tool trusts a path like `../../Users/me/secrets.txt`, the AI (or a malicious prompt) could escape `workspace/` and read or destroy other files. This attack is called **path traversal**.

**The defense.** Every tool that takes a `path` passes it through `_get_safe_path()` first. The function:

1. Joins the requested relative path onto the workspace root.
2. Resolves it to an absolute path (collapsing `..` and following symlinks).
3. Checks that the result is still **inside** the workspace root.
4. Raises an error otherwise, so the tool never touches the file.

Because *all* file tools share this one gate, there is a single place to audit.

### 4.3 Reference `server.py` (Reconstructed)

> Written by Session 4 to match the documented tool set. It has **not** been run against the original deployment. Test it (see section 5) before depending on it.

```python
import subprocess
from pathlib import Path
from fastmcp import FastMCP

WORKSPACE = (Path(__file__).parent / "workspace").resolve()
WORKSPACE.mkdir(exist_ok=True)

mcp = FastMCP("my file server")


def _get_safe_path(relative_path: str) -> Path:
    """Resolve a path and guarantee it stays inside WORKSPACE."""
    candidate = (WORKSPACE / relative_path).resolve()
    if candidate != WORKSPACE and WORKSPACE not in candidate.parents:
        raise ValueError(f"Path escapes workspace: {relative_path}")
    return candidate


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=WORKSPACE, capture_output=True, text=True
    )
    return (result.stdout + result.stderr).strip()


@mcp.tool()
def list_files() -> str:
    """List all files currently tracked inside the workspace sandbox."""
    files = [
        str(p.relative_to(WORKSPACE))
        for p in sorted(WORKSPACE.rglob("*"))
        if p.is_file() and ".git" not in p.parts
    ]
    return "\n".join(files)


@mcp.tool()
def read_file(path: str) -> str:
    """Read and return the plain text contents of a file."""
    return _get_safe_path(path).read_text(encoding="utf-8")


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write or overwrite text content to a file inside the sandbox."""
    target = _get_safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {path}"


@mcp.tool()
def str_replace(path: str, old_str: str, new_str: str) -> str:
    """Replace an exact unique occurrence of old_str with new_str."""
    target = _get_safe_path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old_str)
    if count != 1:
        return f"Error: old_str found {count} times (must be exactly 1)."
    target.write_text(text.replace(old_str, new_str), encoding="utf-8")
    return f"Replaced 1 occurrence in {path}"


@mcp.tool()
def delete_file(path: str) -> str:
    """Safely delete a file inside the sandbox."""
    target = _get_safe_path(path)
    if not target.is_file():
        return f"Error: {path} is not a file."
    target.unlink()
    return f"Deleted {path}"


@mcp.tool()
def search_code(keyword: str) -> str:
    """Search for a keyword inside all non-hidden workspace files."""
    hits = []
    for p in sorted(WORKSPACE.rglob("*")):
        if not p.is_file() or any(part.startswith(".") for part in p.relative_to(WORKSPACE).parts):
            continue
        try:
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if keyword in line:
                    hits.append(f"{p.relative_to(WORKSPACE)}:{n}: {line.strip()}")
        except UnicodeDecodeError:
            continue
    return "\n".join(hits) or "No matches."


@mcp.tool()
def git_status() -> str:
    """Check the Git working tree status inside the workspace."""
    return _git("status")


@mcp.tool()
def git_commit(message: str) -> str:
    """Stage all changes inside workspace and create a Git commit."""
    _git("add", "-A")
    return _git("commit", "-m", message)


if __name__ == "__main__":
    # Serves MCP at http://localhost:8000/mcp
    mcp.run(transport="http", host="0.0.0.0", port=8000)
```

---

## 5. Persistent public deployment

You need **two terminals open at the same time**.

### Terminal 1: run the server
```powershell
cd mcp-file-server
.\venv\Scripts\Activate.ps1      # macOS/Linux: source venv/bin/activate
python server.py
```
Leave it running. It listens on **port 8000**.

### Terminal 2: start the ngrok tunnel with your static domain
```powershell
ngrok http --url=<domain>.ngrok-free.app 8000
```
Replace `<domain>.ngrok-free.app` with the exact domain you claimed (it may end in `.ngrok-free.dev`). On older ngrok versions the flag is `--domain=` instead of `--url=`.

Your MCP endpoint is now:

```
https://<domain>.ngrok-free.app/mcp
```

Because the domain is **static**, this address stays the same every time you restart, so you only configure Claude once.

### Quick check
Open `https://<domain>.ngrok-free.app/mcp` in a browser. An error such as "Not Acceptable" or a protocol message is **normal**: it proves the server is reachable. A connection error means a terminal is not running.

### Connect to Claude (web or desktop)
1. Open Claude and go to **Settings > Connectors**.
2. Click **Add custom connector**.
3. Name it (e.g. `my file server`) and paste `https://<domain>.ngrok-free.app/mcp`.
4. Save, then enable the connector in a chat from the tools/connectors menu.
5. Test with: *"List the files in the workspace."*

(Menu names vary slightly by app version, and custom connectors may require a paid plan.)

> **Security reminder.** Anyone who has your public URL can call your tools. Keep the URL private, stop the tunnel (`Ctrl+C`) when not in use, and never place secrets in `workspace/`.

---

## 6. Multi-session demonstration log

### The idea
Each Claude session starts with **no memory** of earlier ones. To prove work can continue anyway, the sessions coordinated only through two files in the shared workspace:

- **`PROJECT_STATE.md`**: what exists now, what each session did, notes.
- **`PLAN_LOG.md`**: the checklist of completed work and the "Next Step".

Each new session first reads these files, does its work, then updates them for the next session. This is a **handoff protocol**.

### What each session did **[Verified against the logs]**

| Session | Role | Result |
|---------|------|--------|
| 1 | Scaffold | Created `index.html` (`<h1>Items</h1>` and an empty `<ul id='items'>`); created `PROJECT_STATE.md` and `PLAN_LOG.md` |
| 2 | Feature | Created `app.js` to fill the list with "Item 1/2/3"; linked it before `</body>` |
| 3 | Feature | Added click-to-toggle strikethrough per item (found the code via `search_code`); noted it was verified by code inspection only |
| 4 | Documentation | Audited state, wrote this `README.md`, updated both logs, committed |

Session 2 and 3 never saw each other's conversations; Session 3 knew what to build on only because it read what Session 2 wrote.

### Prompts **[Reconstructed]**
The original prompts were not saved. These are faithful reconstructions of each session's task; adapt freely. Run each in a **brand-new chat** with the connector enabled.

**Session 1**
```
Connect to the file server. You are Session 1. Create index.html with a clean HTML5
structure containing an <h1> "Items" and an empty <ul id='items'></ul>. Then create
PROJECT_STATE.md and PLAN_LOG.md describing what you did and what the next session
should do. Commit your work.
```

**Session 2**
```
Connect to the file server. You are Session 2. Read PROJECT_STATE.md and PLAN_LOG.md
first. Then create app.js that selects #items and appends three <li> elements
("Item 1", "Item 2", "Item 3"), and link it in index.html just before </body>.
Update both log files and commit.
```

**Session 3**
```
Connect to the file server. You are Session 3. Read PROJECT_STATE.md and PLAN_LOG.md
first. Use search_code to find the list logic in app.js, then add a click listener to
each <li> that toggles text-decoration: line-through. Do not break index.html.
Update both log files and commit.
```

**Session 4** (the real prompt, summarized)
```
Connect to the file server. You are Session 4, an automated technical documentation
agent. Audit PROJECT_STATE.md, PLAN_LOG.md and list_files. Write a complete,
beginner-friendly README.md. Update PLAN_LOG.md and PROJECT_STATE.md, then commit
with: 'Session 4: Generated comprehensive beginner-friendly README.md via MCP connector'.
```

### How to test continuity yourself
Run the four prompts in four separate chats, in order. After each, ask *"Summarize what the previous sessions did,"* and compare the answer to the logs.

---

## 7. What the demo project contains **[Verified]**

| File | Purpose |
|------|---------|
| `index.html` | Page with an `<h1>Items</h1>` heading and an empty `<ul id='items'>` |
| `app.js` | Fills the list and toggles strikethrough on click |
| `PROJECT_STATE.md` | Current state and per-session notes |
| `PLAN_LOG.md` | Completed-work checklist and next step |
| `DECISIONS.md` | Currently empty (reserved for design decisions) |
| `CHECKPOINTS.md` | Currently empty (reserved for milestones) |
| `README.md` | This file |

**Try it:** double-click `index.html` to open it in your browser, then click each item. A line should appear through it, and clicking again removes it. *(As of Session 3 this had been verified by code inspection only, not in a live browser.)*

---

## 8. Troubleshooting

| Symptom | Likely fix |
|---------|-----------|
| `python` is not recognized | Reinstall Python and tick **Add python.exe to PATH** |
| Activation script blocked | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `pip install` fails | Ensure `(venv)` is showing; update with `python -m pip install --upgrade pip` |
| ngrok: authentication failed | Re-run `ngrok config add-authtoken ...` with the token from your dashboard |
| ngrok: domain not found/unauthorized | Use the exact domain shown in the ngrok dashboard under Domains |
| Claude cannot reach the server | Check both terminals are running and the URL ends in `/mcp` |
| `git_commit` says nothing to commit | No files changed since the last commit; this is normal |
| `git_commit` asks who you are | Run the `git config user.name/user.email` commands from step 3.4 |
