import asyncio
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional
import config


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def human_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


async def list_directory(path: str = None) -> dict:
    path = path or config.STORAGE_DIR
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return {"success": False, "error": f"Path tidak ditemukan: {path}"}
    try:
        entries = []
        for item in sorted(os.listdir(path)):
            full = os.path.join(path, item)
            stat = os.stat(full)
            entries.append({
                "name": item,
                "path": full,
                "type": "dir" if os.path.isdir(full) else "file",
                "size": human_size(stat.st_size) if os.path.isfile(full) else "-",
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            })
        return {"success": True, "path": path, "entries": entries, "count": len(entries)}
    except PermissionError:
        return {"success": False, "error": f"Tidak ada izin untuk mengakses: {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def read_file(filepath: str, max_bytes: int = 500_000) -> dict:
    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        return {"success": False, "error": "File tidak ditemukan"}
    try:
        size = os.path.getsize(filepath)
        if size > max_bytes:
            return {
                "success": False,
                "error": f"File terlalu besar ({human_size(size)}). Maksimum {human_size(max_bytes)}. Gunakan read_file_range()."
            }
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"success": True, "path": filepath, "content": content, "size": size}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def read_file_range(filepath: str, start_line: int = 1, end_line: int = 100) -> dict:
    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        return {"success": False, "error": "File tidak ditemukan"}
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        total = len(lines)
        selected = lines[max(0, start_line - 1):end_line]
        return {
            "success": True,
            "path": filepath,
            "start_line": start_line,
            "end_line": min(end_line, total),
            "total_lines": total,
            "content": "".join(selected),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def write_file(filepath: str, content: str, mode: str = "w") -> dict:
    filepath = os.path.expanduser(filepath)
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, mode, encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": filepath, "size": os.path.getsize(filepath)}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def copy_file(src: str, dest: str) -> dict:
    src = os.path.expanduser(src)
    dest = os.path.expanduser(dest)
    try:
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        shutil.copy2(src, dest)
        return {"success": True, "src": src, "dest": dest}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def move_file(src: str, dest: str) -> dict:
    src = os.path.expanduser(src)
    dest = os.path.expanduser(dest)
    try:
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        shutil.move(src, dest)
        return {"success": True, "src": src, "dest": dest}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def delete_file(filepath: str) -> dict:
    filepath = os.path.expanduser(filepath)
    try:
        if os.path.isdir(filepath):
            shutil.rmtree(filepath)
        else:
            os.remove(filepath)
        return {"success": True, "path": filepath}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def zip_files(paths: list, output: str = None) -> dict:
    if not output:
        output = os.path.join(config.DOWNLOADS_DIR, f"archive_{_timestamp()}.zip")
    output = os.path.expanduser(output)
    try:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in paths:
                p = os.path.expanduser(p)
                if os.path.isfile(p):
                    zf.write(p, os.path.basename(p))
                elif os.path.isdir(p):
                    for root, dirs, files in os.walk(p):
                        for file in files:
                            fp = os.path.join(root, file)
                            arcname = os.path.relpath(fp, os.path.dirname(p))
                            zf.write(fp, arcname)
        size = os.path.getsize(output)
        return {"success": True, "path": output, "size": human_size(size)}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def unzip_file(filepath: str, dest_dir: str = None) -> dict:
    filepath = os.path.expanduser(filepath)
    dest_dir = dest_dir or os.path.join(config.DOWNLOADS_DIR, Path(filepath).stem)
    dest_dir = os.path.expanduser(dest_dir)
    try:
        os.makedirs(dest_dir, exist_ok=True)
        with zipfile.ZipFile(filepath, "r") as zf:
            zf.extractall(dest_dir)
        return {"success": True, "dest": dest_dir, "files": os.listdir(dest_dir)}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def share_file(filepath: str) -> dict:
    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        return {"success": False, "error": "File tidak ditemukan"}
    try:
        proc = await asyncio.create_subprocess_exec(
            "termux-share", filepath,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        if proc.returncode == 0:
            return {"success": True, "path": filepath, "message": "Dialog share Android dibuka"}
        return {"success": False, "error": stderr.decode().strip()}
    except FileNotFoundError:
        return {"success": False, "error": "termux-share tidak ditemukan. Install termux-api."}
    except asyncio.TimeoutError:
        return {"success": False, "error": "Share timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def open_file(filepath: str) -> dict:
    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        return {"success": False, "error": "File tidak ditemukan"}
    try:
        proc = await asyncio.create_subprocess_exec(
            "termux-open", filepath,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=10)
        return {"success": True, "path": filepath}
    except Exception as e:
        return {"success": False, "error": str(e)}
