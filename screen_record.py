import asyncio
import os
import signal
from datetime import datetime
import config

_active_process = None
_active_filepath = None


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def start_recording(
    filename: str = None,
    duration: int = None,
    save_dir: str = None,
    bit_rate: str = None,
    size: str = None,
) -> dict:
    global _active_process, _active_filepath

    if _active_process and _active_process.returncode is None:
        return {"success": False, "error": "Sudah ada rekaman yang sedang berjalan. Hentikan dulu."}

    save_dir = save_dir or config.RECORDINGS_DIR
    os.makedirs(save_dir, exist_ok=True)

    duration = min(duration or config.SCREEN_RECORD_DEFAULT_DURATION, config.SCREEN_RECORD_MAX_DURATION)
    bit_rate = bit_rate or config.SCREEN_RECORD_BIT_RATE
    size_val = size or config.SCREEN_RECORD_SIZE

    if not filename:
        filename = f"recording_{_timestamp()}.mp4"
    elif not filename.endswith(".mp4"):
        filename += ".mp4"

    filepath = os.path.join(save_dir, filename)

    result = await _try_termux_record(filepath, duration)
    if result.get("started") or result.get("success"):
        _active_filepath = filepath
        return result

    result = await _try_screenrecord(filepath, duration, bit_rate, size_val)
    if result.get("started") or result.get("success"):
        _active_filepath = filepath
        return result

    return {
        "success": False,
        "error": (
            "Screen recording gagal. Coba:\n"
            "1. pkg install termux-api\n"
            "2. Install Termux:API dari F-Droid\n"
            "3. Berikan izin 'Display over other apps'\n"
            "Catatan: Beberapa perangkat memerlukan root untuk screenrecord"
        ),
    }


async def _try_termux_record(filepath: str, duration: int) -> dict:
    global _active_process
    try:
        proc = await asyncio.create_subprocess_exec(
            "termux-screen-record", "-o", filepath,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _active_process = proc
        await asyncio.sleep(1)
        if proc.returncode is not None and proc.returncode != 0:
            return {"started": False, "error": "termux-screen-record gagal"}
        return {
            "started": True,
            "success": True,
            "path": filepath,
            "duration": duration,
            "method": "termux-screen-record",
            "message": f"Rekaman dimulai, akan berhenti otomatis setelah {duration}s atau panggil stop_recording()",
        }
    except FileNotFoundError:
        return {"started": False, "error": "termux-screen-record tidak ditemukan"}
    except Exception as e:
        return {"started": False, "error": str(e)}


async def _try_screenrecord(filepath: str, duration: int, bit_rate: str, size_val: str) -> dict:
    global _active_process
    try:
        cmd = [
            "screenrecord",
            "--time-limit", str(duration),
            "--bit-rate", bit_rate,
            "--size", size_val,
            filepath,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _active_process = proc
        await asyncio.sleep(1)
        if proc.returncode is not None and proc.returncode != 0:
            stderr = await proc.stderr.read()
            return {"started": False, "error": f"screenrecord gagal: {stderr.decode().strip()}"}
        return {
            "started": True,
            "success": True,
            "path": filepath,
            "duration": duration,
            "method": "screenrecord",
            "message": f"Rekaman dimulai ({duration}s maks). Hentikan dengan stop_recording()",
        }
    except FileNotFoundError:
        return {"started": False, "error": "screenrecord tidak ditemukan (mungkin perlu root)"}
    except Exception as e:
        return {"started": False, "error": str(e)}


async def stop_recording() -> dict:
    global _active_process, _active_filepath
    if not _active_process:
        return {"success": False, "error": "Tidak ada rekaman yang sedang berjalan"}
    try:
        _active_process.send_signal(signal.SIGINT)
        try:
            await asyncio.wait_for(_active_process.wait(), timeout=5)
        except asyncio.TimeoutError:
            _active_process.kill()
            await _active_process.wait()

        filepath = _active_filepath
        _active_process = None
        _active_filepath = None

        if filepath and os.path.exists(filepath):
            size = os.path.getsize(filepath)
            return {"success": True, "path": filepath, "size": size}
        return {"success": False, "error": "File rekaman tidak ditemukan setelah dihentikan"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def is_recording() -> bool:
    return _active_process is not None and _active_process.returncode is None


async def list_recordings(save_dir: str = None) -> list:
    save_dir = save_dir or config.RECORDINGS_DIR
    if not os.path.exists(save_dir):
        return []
    files = sorted(
        [f for f in os.listdir(save_dir) if f.lower().endswith(".mp4")],
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
            "size_mb": round(stat.st_size / 1024 / 1024, 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return result
