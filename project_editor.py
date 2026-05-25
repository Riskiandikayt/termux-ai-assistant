import asyncio
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
import config

SUPPORTED_CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".kt", ".c", ".cpp", ".h",
    ".go", ".rs", ".rb", ".php", ".swift", ".sh", ".bash", ".zsh", ".fish",
    ".html", ".css", ".scss", ".sass", ".less", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".env", ".md", ".txt", ".xml", ".sql",
    ".r", ".lua", ".dart", ".ex", ".exs", ".erl", ".hs", ".clj", ".scala",
    ".vue", ".svelte", ".astro",
}

IGNORED_DIRS = {
    ".git", ".svn", "node_modules", "__pycache__", ".cache", "dist",
    "build", ".gradle", ".idea", ".vscode", "venv", ".venv", "env",
    "target", "out", ".dart_tool", ".flutter-plugins",
}


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def read_project_structure(project_path: str, max_depth: int = 5) -> dict:
    project_path = os.path.expanduser(project_path)
    if not os.path.exists(project_path):
        return {"success": False, "error": f"Path tidak ditemukan: {project_path}"}

    lines = []

    def walk(path, depth, prefix=""):
        if depth > max_depth:
            return
        try:
            items = sorted(os.listdir(path))
        except PermissionError:
            return

        dirs = [i for i in items if os.path.isdir(os.path.join(path, i)) and i not in IGNORED_DIRS]
        files = [i for i in items if os.path.isfile(os.path.join(path, i))]

        all_items = dirs + files
        for i, item in enumerate(all_items):
            is_last = i == len(all_items) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{item}")
            if os.path.isdir(os.path.join(path, item)) and item not in IGNORED_DIRS:
                extension = "    " if is_last else "│   "
                walk(os.path.join(path, item), depth + 1, prefix + extension)

    lines.append(os.path.basename(project_path) + "/")
    walk(project_path, 1)
    return {"success": True, "path": project_path, "tree": "\n".join(lines)}


async def read_project_files(project_path: str, extensions: list = None, max_file_size: int = 100_000) -> dict:
    project_path = os.path.expanduser(project_path)
    if not os.path.exists(project_path):
        return {"success": False, "error": f"Path tidak ditemukan: {project_path}"}

    allowed_ext = set(extensions) if extensions else SUPPORTED_CODE_EXTENSIONS
    files_content = {}
    skipped = []

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext not in allowed_ext:
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, project_path)
            size = os.path.getsize(fpath)
            if size > max_file_size:
                skipped.append({"file": rel, "reason": f"terlalu besar ({size // 1024}KB)"})
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    files_content[rel] = f.read()
            except Exception as e:
                skipped.append({"file": rel, "reason": str(e)})

    return {
        "success": True,
        "path": project_path,
        "files": files_content,
        "count": len(files_content),
        "skipped": skipped,
    }


async def create_file(filepath: str, content: str) -> dict:
    filepath = os.path.expanduser(filepath)
    if os.path.exists(filepath):
        backup = filepath + f".bak_{_timestamp()}"
        shutil.copy2(filepath, backup)
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": filepath, "size": os.path.getsize(filepath)}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def edit_file(filepath: str, old_content: str, new_content: str) -> dict:
    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        return {"success": False, "error": "File tidak ditemukan"}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            current = f.read()
        if old_content not in current:
            return {
                "success": False,
                "error": "Konten lama tidak ditemukan dalam file. Pastikan teks yang ingin diganti persis sama.",
            }
        backup = filepath + f".bak_{_timestamp()}"
        shutil.copy2(filepath, backup)
        new = current.replace(old_content, new_content, 1)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new)
        return {"success": True, "path": filepath, "backup": backup}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def replace_lines(filepath: str, start_line: int, end_line: int, new_content: str) -> dict:
    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        return {"success": False, "error": "File tidak ditemukan"}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        backup = filepath + f".bak_{_timestamp()}"
        shutil.copy2(filepath, backup)
        new_lines = new_content if new_content.endswith("\n") else new_content + "\n"
        lines[start_line - 1:end_line] = [new_lines]
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return {"success": True, "path": filepath, "backup": backup}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def append_to_file(filepath: str, content: str) -> dict:
    filepath = os.path.expanduser(filepath)
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": filepath}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def search_in_project(project_path: str, pattern: str, file_pattern: str = None) -> dict:
    project_path = os.path.expanduser(project_path)
    if not os.path.exists(project_path):
        return {"success": False, "error": f"Path tidak ditemukan: {project_path}"}

    results = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return {"success": False, "error": f"Regex tidak valid: {e}"}

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for fname in files:
            if file_pattern and not fname.endswith(file_pattern):
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, project_path)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    for lineno, line in enumerate(f, 1):
                        if regex.search(line):
                            results.append({
                                "file": rel,
                                "line": lineno,
                                "content": line.rstrip(),
                            })
            except Exception:
                continue

    return {"success": True, "pattern": pattern, "results": results, "count": len(results)}


async def restore_backup(backup_path: str) -> dict:
    backup_path = os.path.expanduser(backup_path)
    if not os.path.exists(backup_path):
        return {"success": False, "error": "Backup tidak ditemukan"}
    original = re.sub(r"\.bak_\d{8}_\d{6}$", "", backup_path)
    try:
        shutil.copy2(backup_path, original)
        os.remove(backup_path)
        return {"success": True, "restored": original}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def run_command(command: str, cwd: str = None, timeout: int = 30) -> dict:
    cwd = os.path.expanduser(cwd) if cwd else None
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }
    except asyncio.TimeoutError:
        proc.kill()
        return {"success": False, "error": f"Command timeout setelah {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}
