import os
import subprocess
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# 1. Initialize the Server
mcp = FastMCP("SecureFileServer")

# 2. Set up the Sandboxed Workspace Root
WORKSPACE_ROOT = Path("./workspace").resolve()
WORKSPACE_ROOT.mkdir(exist_ok=True)

def _get_safe_path(rel_path: str) -> Path:
    """Security check to ensure agents cannot access files outside the workspace folder."""
    target_path = (WORKSPACE_ROOT / rel_path).resolve()
    if not target_path.is_relative_to(WORKSPACE_ROOT):
        raise ValueError("Security violation: Access denied to path outside sandbox.")
    return target_path

# 3. Define the 8 Required Tools

@mcp.tool()
def list_files() -> list[str]:
    """List all files and directories recursively inside the workspace."""
    return [str(p.relative_to(WORKSPACE_ROOT)) for p in WORKSPACE_ROOT.rglob("*") if p.is_file()]

@mcp.tool()
def read_file(path: str = Field(description="Name of the file to read")) -> str:
    """Read the text content of a file."""
    safe_path = _get_safe_path(path)
    if not safe_path.exists():
        return f"Error: File {path} not found."
    return safe_path.read_text(encoding="utf-8")

@mcp.tool()
def write_file(path: str = Field(description="Name of the file to write"), 
               content: str = Field(description="Text content to save")) -> str:
    """Create or overwrite a file with new text content."""
    safe_path = _get_safe_path(path)
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    safe_path.write_text(content, encoding="utf-8")
    return f"Success: Wrote data to {path}"

@mcp.tool()
def str_replace(path: str, old_str: str, new_str: str) -> str:
    """Replace an exact word or phrase in a file. Fails if the phrase appears multiple times."""
    safe_path = _get_safe_path(path)
    content = safe_path.read_text(encoding="utf-8")
    count = content.count(old_str)
    if count == 0:
        return f"Error: '{old_str}' not found in {path}."
    if count > 1:
        return f"Error: '{old_str}' appears {count} times. You must be more specific."
    
    new_content = content.replace(old_str, new_str)
    safe_path.write_text(new_content, encoding="utf-8")
    return f"Success: Updated text in {path}"

@mcp.tool()
def delete_file(path: str) -> str:
    """Delete a file from the workspace."""
    safe_path = _get_safe_path(path)
    if safe_path.is_file():
        safe_path.unlink()
        return f"Success: Deleted {path}"
    return f"Error: Cannot delete {path}."

@mcp.tool()
def search_code(keyword: str) -> str:
    """Search for a specific keyword inside all files in the workspace."""
    results = []
    for filepath in WORKSPACE_ROOT.rglob("*"):
        if filepath.is_file():
            try:
                content = filepath.read_text(encoding="utf-8")
                if keyword in content:
                    results.append(str(filepath.relative_to(WORKSPACE_ROOT)))
            except UnicodeDecodeError:
                continue
    if not results:
        return f"No files found containing '{keyword}'."
    return f"Found '{keyword}' in: " + ", ".join(results)

@mcp.tool()
def git_status() -> str:
    """Check the status of tracked and untracked files in the workspace."""
    try:
        result = subprocess.run(["git", "status", "-s"], cwd=WORKSPACE_ROOT, capture_output=True, text=True)
        return result.stdout if result.stdout else "Working directory clean."
    except Exception as e:
        return f"Git error: {str(e)}"

@mcp.tool()
def git_commit(message: str) -> str:
    """Stage all changes and commit them with a descriptive message."""
    try:
        subprocess.run(["git", "add", "."], cwd=WORKSPACE_ROOT, check=True)
        subprocess.run(["git", "commit", "-m", message], cwd=WORKSPACE_ROOT, check=True)
        return f"Success: Committed changes with message: '{message}'"
    except Exception as e:
        return f"Git commit failed: Ensure git is initialized. Error: {str(e)}"

if __name__ == "__main__":
    # Start the server using Streamable HTTP on port 8000
    mcp.run(transport="sse", host="0.0.0.0", port=8000)