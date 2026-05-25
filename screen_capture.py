import asyncio
import os
import subprocess
from datetime import datetime
from pathlib import Path
import config


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def take_screenshot(filename: str = None, save_dir: str = None) -> dict:
    save_dir = save_dir or config.SCREENSHOTS_DIR
    os.makedirs(save_dir, exist_ok=True)

    if not filename:
        filename = f"screenshot_{_timestamp()}.png"
    elif not filename.endswith(".png"):
        filename += ".png"

    filepath = os.path.join(save_dir, filename)

    result = await _try_termux_screenshot(filepath)
    if result["success"]:
        return result

    result = await _try_screencap(filepath)
    if result["success"]:
        return result

    return {
        "success": False,
        "path": None,
        "error": (
            "Screenshot gagal. Coba:\n"
            "1. Pastikan termux-api terinstall: pkg install termux-api\n"
            "2. Pastikan app Termux:API terinstall dari F-Droid\n"
            "3. Berikan izin 'Display over other apps' ke Termux:API"
        ),
    }


async def _try_termux_screenshot(filepath: str) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            "termux-screenshot", "-s", filepath,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        if proc.returncode == 0 and os.path.exists(filepath):
            size = os.path.getsize(filepath)
            return {"success": True, "path": filepath, "size": size, "method": "termux-screenshot"}
        return {"success": False, "error": stderr.decode().strip()}
    except FileNotFoundError:
        return {"success": False, "error": "termux-screenshot tidak ditemukan"}
    except asyncio.TimeoutError:
        return {"success": False, "error": "termux-screenshot timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _try_screencap(filepath: str) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            "screencap", "-p", filepath,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        if proc.returncode == 0 and os.path.exists(filepath):
            size = os.path.getsize(filepath)
            return {"success": True, "path": filepath, "size": size, "method": "screencap"}
        return {"success": False, "error": stderr.decode().strip()}
    except FileNotFoundError:
        return {"success": False, "error": "screencap tidak ditemukan"}
    except asyncio.TimeoutError:
        return {"success": False, "error": "screencap timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def list_screenshots(save_dir: str = None) -> list:
    save_dir = save_dir or config.SCREENSHOTS_DIR
    if not os.path.exists(save_dir):
        return []
    files = sorted(
        [f for f in os.listdir(save_dir) if f.lower().endswith(".png")],
        reverse=True,
    )
    result = []
    for f in files:
        fp = os.path.join(save_dir, f)
        stat = os.stat(fp)
        result.append({
            "name": f,
            "path": fp,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return result


async def delete_screenshot(filepath: str) -> dict:
    try:
        if not os.path.exists(filepath):
            return {"success": False, "error": "File tidak ditemukan"}
        os.remove(filepath)
        return {"success": True, "path": filepath}
    except Exception as e:
        return {"success": False, "error": str(e)}
