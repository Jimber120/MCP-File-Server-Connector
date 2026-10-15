import os
import subprocess
from pathlib import Path
from mcp.server.mcpserver import MCPServer
from pydantic import Field

# 1. Initialize the MCP 2.x Server
mcp = MCPServer("SecureFileServer")

# 2. Pin the Sandboxed Workspace Root to the explicit folder created in Phase 2
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = (BASE_DIR / "workspace").resolve()

# Fallback: ensure the folder exists if deleted
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

def _get_safe_path(rel_path: str) -> Path:
    """
    Resolves the target file path and strictly enforces that it cannot
    escape WORKSPACE_ROOT (defends against directory traversal like ../../).
    """
    clean_rel = rel_path.lstrip("/\\")
    target_path = (WORKSPACE_ROOT / clean_rel).resolve()
    
    if not target_path.is_relative_to(WORKSPACE_ROOT):
        raise PermissionError(f"Security violation: Access denied outside sandbox: {rel_path}")
    return target_path

# ==========================================================
# 3. Implement the 8 Required Tools
# ==========================================================

# Tool 1: list_files
@mcp.tool()
def list_files() -> list[str]:
    """List all files currently tracked inside the workspace sandbox."""
    return [
        str(p.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
        for p in WORKSPACE_ROOT.rglob("*")
        if p.is_file() and not p.parts[len(WORKSPACE_ROOT.parts):][0].startswith(".git")
    ]

# Tool 2: read_file
@mcp.tool()
def read_file(path: str = Field(description="Relative path of the file to read")) -> str:
    """Read and return the plain text contents of a file."""
    safe_path = _get_safe_path(path)
    if not safe_path.exists():
        return f"Error: File '{path}' does not exist."
    return safe_path.read_text(encoding="utf-8")

# Tool 3: write_file
@mcp.tool()
def write_file(
    path: str = Field(description="Relative path of the file to write"),
    content: str = Field(description="Exact text content to write")
) -> str:
    """Write or overwrite text content to a file inside the sandbox."""
    safe_path = _get_safe_path(path)
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    safe_path.write_text(content, encoding="utf-8")
    return f"Success: Wrote {len(content)} characters to '{path}'."

# Tool 4: str_replace
@mcp.tool()
def str_replace(
    path: str = Field(description="Relative path to file"),
    old_str: str = Field(description="Exact string snippet to match"),
    new_str: str = Field(description="Replacement string")
) -> str:
    """Replace an exact unique occurrence of old_str with new_str."""
    safe_path = _get_safe_path(path)
    if not safe_path.exists():
        return f"Error: File '{path}' does not exist."
    
    content = safe_path.read_text(encoding="utf-8")
    matches = content.count(old_str)
    
    if matches == 0:
        return f"Error: '{old_str}' not found in '{path}'."
    if matches > 1:
        return f"Error: '{old_str}' matches {matches} occurrences. Make old_str more specific."
    
    updated_content = content.replace(old_str, new_str, 1)
    safe_path.write_text(updated_content, encoding="utf-8")
    return f"Success: Replaced occurrence in '{path}'."

# Tool 5: delete_file
@mcp.tool()
def delete_file(path: str = Field(description="Relative path of file to delete")) -> str:
    """Safely delete a file inside the sandbox."""
    safe_path = _get_safe_path(path)
    if safe_path.is_file():
        safe_path.unlink()
        return f"Success: File '{path}' deleted."
    return f"Error: Cannot delete '{path}'. File not found."

# Tool 6: search_code
@mcp.tool()
def search_code(keyword: str = Field(description="Sub-string to search across files")) -> str:
    """Search for a keyword inside all non-hidden workspace files."""
    matches = []
    for filepath in WORKSPACE_ROOT.rglob("*"):
        if filepath.is_file() and not any(part.startswith(".") for part in filepath.parts):
            try:
                text = filepath.read_text(encoding="utf-8", errors="ignore")
                if keyword in text:
                    rel = str(filepath.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
                    matches.append(rel)
            except Exception:
                continue
    if not matches:
        return f"No matches found for '{keyword}'."
    return f"Found '{keyword}' in: " + ", ".join(matches)

# Tool 7: git_status
@mcp.tool()
def git_status() -> str:
    """Check the Git working tree status inside the workspace."""
    try:
        proc = subprocess.run(
            ["git", "status", "--short"],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        output = proc.stdout.strip()
        return output if output else "Workspace clean. No uncommitted changes."
    except Exception as e:
        return f"Git error: {str(e)}"

# Tool 8: git_commit
@mcp.tool()
def git_commit(message: str = Field(description="Commit message")) -> str:
    """Stage all changes inside workspace and create a Git commit."""
    try:
        subprocess.run(["git", "add", "."], cwd=WORKSPACE_ROOT, check=True)
        proc = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True
        )
        return proc.stdout.strip() if proc.stdout else "Commit complete."
    except Exception as e:
        return f"Commit error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)