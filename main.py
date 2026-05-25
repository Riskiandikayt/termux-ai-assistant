#!/usr/bin/env python3
"""
AI Assistant untuk Termux Android
Jalankan: python main.py
"""

import asyncio
import os
import sys
import readline
from typing import Optional

import config
from ai_client import AIClient
from screen_capture import take_screenshot, list_screenshots
from screen_record import start_recording, stop_recording, is_recording, list_recordings
from file_sender import (
    list_directory, read_file, write_file, copy_file,
    move_file, delete_file, zip_files, unzip_file, share_file,
)
from project_editor import (
    read_project_structure, read_project_files, create_file,
    edit_file, search_in_project, run_command, restore_backup,
)

BANNER = """
╔══════════════════════════════════════════════╗
║        AI Assistant — Termux Android         ║
║  Model: llama.cpp / Ollama (lokal, gratis)   ║
╚══════════════════════════════════════════════╝
Ketik /help untuk daftar perintah.
"""

HELP_TEXT = """
━━━━━━━━━━━━━━━━ PERINTAH ━━━━━━━━━━━━━━━━

CHAT
  /chat <pesan>          Chat langsung dengan AI
  /ask <file> <tanya>    Tanya AI tentang isi file
  /code <deskripsi>      Minta AI generate kode
  /debug <file>          Minta AI debug file kode
  /review <file>         Minta AI review kode

SCREENSHOT
  /screenshot            Ambil screenshot sekarang
  /screenshots           Daftar screenshot tersimpan
  /share-ss <path>       Share screenshot via Android

REKAMAN LAYAR
  /record [detik]        Mulai rekam layar (default 30s)
  /record-stop           Hentikan rekaman
  /recordings            Daftar rekaman tersimpan

FILE & STORAGE
  /ls [path]             Lihat isi folder
  /read <path>           Baca isi file
  /write <path>          Tulis file (ketik konten, akhiri dengan EOF)
  /copy <src> <dest>     Copy file
  /move <src> <dest>     Pindah file
  /del <path>            Hapus file
  /zip <dest> <f1> <f2>  Zip beberapa file
  /unzip <zip> [dest]    Ekstrak zip
  /share <path>          Share file via Android

PROJECT
  /tree <path>           Tampilkan struktur folder project
  /scan <path>           Baca semua file kode dalam project
  /search <path> <pola>  Cari teks dalam project
  /new <path>            Buat file baru (ketik konten, akhiri EOF)
  /edit <path>           Edit file (panduan interaktif)
  /run <cmd>             Jalankan shell command

LAINNYA
  /backend <n>           Ganti AI backend (llamacpp/ollama)
  /status                Cek status AI server
  /clear                 Bersihkan layar
  /help                  Tampilkan bantuan ini
  /exit                  Keluar

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

CODING_SYSTEM = """Kamu adalah coding assistant yang ahli. Selalu berikan:
1. Kode yang lengkap dan siap pakai
2. Penjelasan singkat di atas kode
3. Petunjuk penggunaan jika perlu
Gunakan bahasa Indonesia. Jangan potong kode."""

CHAT_HISTORY = []


def print_color(text: str, color: str = "white"):
    colors = {
        "red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m",
        "blue": "\033[94m", "magenta": "\033[95m", "cyan": "\033[96m",
        "white": "\033[97m", "reset": "\033[0m", "bold": "\033[1m",
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")


def print_separator():
    print_color("─" * 48, "blue")


async def stream_ai_response(prompt: str, system: str = None, client: AIClient = None):
    client = client or AIClient()
    print_color("\n🤖 AI:", "cyan")
    print_color("─" * 40, "blue")
    full = []
    async for token in client.chat_stream(prompt, system):
        print(token, end="", flush=True)
        full.append(token)
    print("\n")
    return "".join(full)


async def read_multiline_input(prompt: str = "Ketik konten (akhiri dengan baris 'EOF'):") -> str:
    print_color(prompt, "yellow")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "EOF":
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines)


async def handle_command(cmd: str, client: AIClient) -> bool:
    parts = cmd.strip().split(maxsplit=2)
    if not parts:
        return True

    command = parts[0].lower()

    if command in ("/exit", "/quit", "/q"):
        print_color("Sampai jumpa! 👋", "green")
        return False

    elif command == "/help":
        print(HELP_TEXT)

    elif command == "/clear":
        os.system("clear")
        print(BANNER)

    elif command == "/status":
        ready = await client.is_server_ready()
        if ready:
            print_color(f"✅ Backend '{config.AI_BACKEND}' siap.", "green")
        else:
            print_color(f"❌ Backend '{config.AI_BACKEND}' tidak merespons.", "red")
            if config.AI_BACKEND == "llamacpp":
                print_color("Jalankan: ./llama-server -m models/<model>.gguf --host 127.0.0.1 --port 8080", "yellow")
            elif config.AI_BACKEND == "ollama":
                print_color("Jalankan: ollama serve", "yellow")

    elif command == "/backend":
        if len(parts) < 2:
            print_color(f"Backend saat ini: {config.AI_BACKEND}", "cyan")
            print_color("Pilihan: llamacpp, ollama", "yellow")
        else:
            b = parts[1].lower()
            if b in ("llamacpp", "ollama"):
                config.AI_BACKEND = b
                client.backend = b
                print_color(f"✅ Backend diganti ke: {b}", "green")
            else:
                print_color("Backend tidak dikenal. Pilihan: llamacpp, ollama", "red")

    elif command == "/chat":
        if len(parts) < 2:
            print_color("Penggunaan: /chat <pesan>", "red")
        else:
            prompt = cmd[len("/chat "):].strip()
            await stream_ai_response(prompt, client=client)

    elif command == "/code":
        if len(parts) < 2:
            print_color("Penggunaan: /code <deskripsi kode yang diinginkan>", "red")
        else:
            prompt = cmd[len("/code "):].strip()
            await stream_ai_response(prompt, system=CODING_SYSTEM, client=client)

    elif command == "/ask":
        if len(parts) < 3:
            print_color("Penggunaan: /ask <path_file> <pertanyaan>", "red")
        else:
            filepath = parts[1]
            question = parts[2] if len(parts) > 2 else cmd.split(maxsplit=2)[2]
            result = await read_file(filepath)
            if not result["success"]:
                print_color(f"❌ {result['error']}", "red")
            else:
                prompt = f"File: {filepath}\n\nIsi file:\n```\n{result['content']}\n```\n\nPertanyaan: {question}"
                await stream_ai_response(prompt, system=CODING_SYSTEM, client=client)

    elif command == "/debug":
        if len(parts) < 2:
            print_color("Penggunaan: /debug <path_file>", "red")
        else:
            filepath = parts[1]
            result = await read_file(filepath)
            if not result["success"]:
                print_color(f"❌ {result['error']}", "red")
            else:
                prompt = (
                    f"Tolong debug kode berikut dari file `{filepath}`.\n"
                    f"Temukan bug, error potensial, dan berikan perbaikannya:\n\n"
                    f"```\n{result['content']}\n```"
                )
                await stream_ai_response(prompt, system=CODING_SYSTEM, client=client)

    elif command == "/review":
        if len(parts) < 2:
            print_color("Penggunaan: /review <path_file>", "red")
        else:
            filepath = parts[1]
            result = await read_file(filepath)
            if not result["success"]:
                print_color(f"❌ {result['error']}", "red")
            else:
                prompt = (
                    f"Tolong review kode berikut dari file `{filepath}`.\n"
                    f"Berikan feedback tentang kualitas kode, best practice, dan saran perbaikan:\n\n"
                    f"```\n{result['content']}\n```"
                )
                await stream_ai_response(prompt, system=CODING_SYSTEM, client=client)

    elif command == "/screenshot":
        print_color("📸 Mengambil screenshot...", "yellow")
        result = await take_screenshot()
        if result["success"]:
            print_color(f"✅ Screenshot disimpan: {result['path']}", "green")
            print_color(f"   Ukuran: {result['size']:,} bytes | Metode: {result['method']}", "cyan")
        else:
            print_color(f"❌ {result['error']}", "red")

    elif command == "/screenshots":
        files = await list_screenshots()
        if not files:
            print_color("Belum ada screenshot.", "yellow")
        else:
            print_color(f"\n📷 {len(files)} screenshot:", "cyan")
            for f in files[:20]:
                print(f"  {f['modified']}  {f['name']}  ({f['size']:,}B)")

    elif command == "/share-ss":
        if len(parts) < 2:
            print_color("Penggunaan: /share-ss <path>", "red")
        else:
            result = await share_file(parts[1])
            if result["success"]:
                print_color(f"✅ {result['message']}", "green")
            else:
                print_color(f"❌ {result['error']}", "red")

    elif command == "/record":
        if is_recording():
            print_color("⚠️  Sudah ada rekaman berjalan. Gunakan /record-stop.", "yellow")
        else:
            duration = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else config.SCREEN_RECORD_DEFAULT_DURATION
            print_color(f"🎥 Memulai rekaman layar ({duration}s)...", "yellow")
            result = await start_recording(duration=duration)
            if result.get("success"):
                print_color(f"✅ {result['message']}", "green")
                print_color(f"   Disimpan ke: {result['path']}", "cyan")
            else:
                print_color(f"❌ {result.get('error', 'Gagal memulai rekaman')}", "red")

    elif command == "/record-stop":
        if not is_recording():
            print_color("Tidak ada rekaman yang berjalan.", "yellow")
        else:
            print_color("⏹  Menghentikan rekaman...", "yellow")
            result = await stop_recording()
            if result["success"]:
                print_color(f"✅ Rekaman disimpan: {result['path']}", "green")
                print_color(f"   Ukuran: {result['size']:,} bytes", "cyan")
            else:
                print_color(f"❌ {result['error']}", "red")

    elif command == "/recordings":
        files = await list_recordings()
        if not files:
            print_color("Belum ada rekaman.", "yellow")
        else:
            print_color(f"\n🎬 {len(files)} rekaman:", "cyan")
            for f in files[:20]:
                print(f"  {f['modified']}  {f['name']}  ({f['size_mb']}MB)")

    elif command == "/ls":
        path = parts[1] if len(parts) > 1 else None
        result = await list_directory(path)
        if not result["success"]:
            print_color(f"❌ {result['error']}", "red")
        else:
            print_color(f"\n📁 {result['path']} ({result['count']} item):", "cyan")
            for e in result["entries"]:
                icon = "📁" if e["type"] == "dir" else "📄"
                print(f"  {icon} {e['name']:<40} {e['size']:<10} {e['modified']}")

    elif command == "/read":
        if len(parts) < 2:
            print_color("Penggunaan: /read <path>", "red")
        else:
            result = await read_file(parts[1])
            if not result["success"]:
                print_color(f"❌ {result['error']}", "red")
            else:
                print_color(f"\n📄 {parts[1]} ({result['size']:,} bytes):", "cyan")
                print_separator()
                print(result["content"])
                print_separator()

    elif command == "/write":
        if len(parts) < 2:
            print_color("Penggunaan: /write <path>", "red")
        else:
            content = await read_multiline_input()
            result = await write_file(parts[1], content)
            if result["success"]:
                print_color(f"✅ File ditulis: {result['path']} ({result['size']:,}B)", "green")
            else:
                print_color(f"❌ {result['error']}", "red")

    elif command == "/copy":
        if len(parts) < 3:
            print_color("Penggunaan: /copy <src> <dest>", "red")
        else:
            result = await copy_file(parts[1], parts[2])
            if result["success"]:
                print_color(f"✅ Disalin: {parts[1]} → {parts[2]}", "green")
            else:
                print_color(f"❌ {result['error']}", "red")

    elif command == "/move":
        if len(parts) < 3:
            print_color("Penggunaan: /move <src> <dest>", "red")
        else:
            result = await move_file(parts[1], parts[2])
            if result["success"]:
                print_color(f"✅ Dipindah: {parts[1]} → {parts[2]}", "green")
            else:
                print_color(f"❌ {result['error']}", "red")

    elif command == "/del":
        if len(parts) < 2:
            print_color("Penggunaan: /del <path>", "red")
        else:
            confirm = input(f"⚠️  Hapus '{parts[1]}'? (y/N): ").strip().lower()
            if confirm == "y":
                result = await delete_file(parts[1])
                if result["success"]:
                    print_color(f"✅ Dihapus: {parts[1]}", "green")
                else:
                    print_color(f"❌ {result['error']}", "red")
            else:
                print_color("Dibatalkan.", "yellow")

    elif command == "/zip":
        if len(parts) < 3:
            print_color("Penggunaan: /zip <output.zip> <file1> [file2...]", "red")
        else:
            dest = parts[1]
            files = cmd.split()[2:]
            result = await zip_files(files, dest)
            if result["success"]:
                print_color(f"✅ Zip dibuat: {result['path']} ({result['size']})", "green")
            else:
                print_color(f"❌ {result['error']}", "red")

    elif command == "/unzip":
        if len(parts) < 2:
            print_color("Penggunaan: /unzip <file.zip> [dest_dir]", "red")
        else:
            dest = parts[2] if len(parts) > 2 else None
            result = await unzip_file(parts[1], dest)
            if result["success"]:
                print_color(f"✅ Diekstrak ke: {result['dest']}", "green")
            else:
                print_color(f"❌ {result['error']}", "red")

    elif command == "/share":
        if len(parts) < 2:
            print_color("Penggunaan: /share <path>", "red")
        else:
            result = await share_file(parts[1])
            if result["success"]:
                print_color(f"✅ {result['message']}", "green")
            else:
                print_color(f"❌ {result['error']}", "red")

    elif command == "/tree":
        if len(parts) < 2:
            print_color("Penggunaan: /tree <path_project>", "red")
        else:
            result = await read_project_structure(parts[1])
            if result["success"]:
                print_color(f"\n🌳 Struktur project: {parts[1]}", "cyan")
                print(result["tree"])
            else:
                print_color(f"❌ {result['error']}", "red")

    elif command == "/scan":
        if len(parts) < 2:
            print_color("Penggunaan: /scan <path_project>", "red")
        else:
            print_color(f"🔍 Membaca file kode di {parts[1]}...", "yellow")
            result = await read_project_files(parts[1])
            if not result["success"]:
                print_color(f"❌ {result['error']}", "red")
            else:
                print_color(f"✅ {result['count']} file ditemukan", "green")
                if result["skipped"]:
                    print_color(f"⚠️  {len(result['skipped'])} file dilewati", "yellow")
                for fname in list(result["files"].keys())[:30]:
                    print(f"  📄 {fname}")
                if result["count"] > 30:
                    print_color(f"  ... dan {result['count'] - 30} file lainnya", "cyan")

    elif command == "/search":
        if len(parts) < 3:
            print_color("Penggunaan: /search <path> <pola>", "red")
        else:
            result = await search_in_project(parts[1], parts[2])
            if not result["success"]:
                print_color(f"❌ {result['error']}", "red")
            else:
                print_color(f"\n🔎 {result['count']} hasil untuk '{parts[2]}':", "cyan")
                for r in result["results"][:50]:
                    print(f"  {r['file']}:{r['line']}  {r['content'][:80]}")

    elif command == "/new":
        if len(parts) < 2:
            print_color("Penggunaan: /new <path>", "red")
        else:
            print_color(f"Membuat file baru: {parts[1]}", "cyan")
            content = await read_multiline_input()
            result = await create_file(parts[1], content)
            if result["success"]:
                print_color(f"✅ File dibuat: {result['path']}", "green")
            else:
                print_color(f"❌ {result['error']}", "red")

    elif command == "/edit":
        if len(parts) < 2:
            print_color("Penggunaan: /edit <path>", "red")
        else:
            print_color("Masukkan teks LAMA yang ingin diganti (akhiri dengan EOF):", "yellow")
            old = await read_multiline_input("")
            print_color("Masukkan teks BARU (akhiri dengan EOF):", "yellow")
            new = await read_multiline_input("")
            result = await edit_file(parts[1], old, new)
            if result["success"]:
                print_color(f"✅ File diedit. Backup: {result['backup']}", "green")
            else:
                print_color(f"❌ {result['error']}", "red")

    elif command == "/run":
        if len(parts) < 2:
            print_color("Penggunaan: /run <command>", "red")
        else:
            shell_cmd = cmd[len("/run "):].strip()
            print_color(f"🔧 Menjalankan: {shell_cmd}", "yellow")
            result = await run_command(shell_cmd)
            if result["stdout"]:
                print(result["stdout"])
            if result["stderr"]:
                print_color(result["stderr"], "red")
            color = "green" if result["success"] else "red"
            print_color(f"Exit code: {result['returncode']}", color)

    else:
        if cmd.startswith("/"):
            print_color(f"Perintah tidak dikenal: {command}. Ketik /help", "red")
        else:
            await stream_ai_response(cmd, client=client)

    return True


async def main():
    print(BANNER)

    client = AIClient()

    ready = await client.is_server_ready()
    if ready:
        print_color(f"✅ AI backend '{config.AI_BACKEND}' siap.", "green")
    else:
        print_color(f"⚠️  AI backend '{config.AI_BACKEND}' tidak merespons.", "yellow")
        if config.AI_BACKEND == "llamacpp":
            print_color("   Jalankan: ./llama-server -m models/<model>.gguf --host 127.0.0.1 --port 8080", "yellow")
        elif config.AI_BACKEND == "ollama":
            print_color("   Jalankan: ollama serve", "yellow")
        print_color("   Tetap bisa pakai perintah file/screenshot/record.", "cyan")

    print()

    while True:
        try:
            if is_recording():
                prompt_text = "\033[91m[REC] \033[97m> "
            else:
                prompt_text = "\033[94m> \033[97m"

            user_input = input(prompt_text).strip()

            if not user_input:
                continue

            should_continue = await handle_command(user_input, client)
            if not should_continue:
                break

        except KeyboardInterrupt:
            print()
            print_color("Tekan Ctrl+C lagi atau ketik /exit untuk keluar.", "yellow")
        except EOFError:
            print()
            break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_color("\nKeluar.", "yellow")
