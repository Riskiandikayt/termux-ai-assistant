# AI Assistant untuk Termux Android

AI assistant multifungsi yang berjalan **100% offline** di Android via Termux. Tidak perlu API key, tidak perlu internet setelah setup, gratis selamanya.

---

## Fitur

| Fitur | Keterangan |
|---|---|
| 💬 AI Chat | Chat dengan model lokal (TinyLlama/Qwen/Phi) |
| 📸 Screenshot | Ambil screenshot langsung dari Termux |
| 🎥 Rekam Layar | Record layar Android |
| 📁 File Manager | Baca, tulis, copy, zip, share file |
| 💻 Coding Assistant | Generate, edit, debug, review kode |
| 🔍 Project Scanner | Baca seluruh project kode sekaligus |

---

## Perangkat yang Didukung

- Android 11+ (dioptimalkan untuk Oppo A92)
- Snapdragon 665 atau setara
- RAM 4GB+ (disarankan 8GB untuk model lebih besar)
- Storage 2GB+ kosong

---

## Model AI (Tanpa API Key)

| Model | RAM | Kecepatan | Kualitas |
|---|---|---|---|
| TinyLlama 1.1B Q4_K_M | ~600MB | ⚡⚡⚡ Sangat cepat | ★★★☆☆ |
| Qwen2.5-0.5B Q4 | ~400MB | ⚡⚡⚡ Paling cepat | ★★☆☆☆ |
| Phi-3-mini Q4 | ~2.2GB | ⚡⚡ Cepat | ★★★★☆ |

**Rekomendasi Oppo A92:** TinyLlama 1.1B Q4_K_M

---

## Instalasi Step-by-Step

### Langkah 0 — Persiapan

1. Install **Termux** dari [F-Droid](https://f-droid.org/packages/com.termux/) (bukan Play Store)
2. Install **Termux:API** dari [F-Droid](https://f-droid.org/packages/com.termux.api/)
3. Buka Termux

### Langkah 1 — Upload/Extract Project

```bash
# Jika dapat file ZIP, extract dulu:
cd ~
unzip /sdcard/Download/termux-ai-assistant.zip
cd termux-ai-assistant
```

### Langkah 2 — Jalankan Installer Otomatis

```bash
bash install.sh
```

Script ini akan otomatis:
- Update dan install paket Termux
- Install Python + dependensi
- Kompilasi llama.cpp (5-10 menit, sekali saja)
- Download model TinyLlama (~670MB)
- Setup folder penyimpanan

### Langkah 3 — Aktifkan Izin Android

Setelah `termux-setup-storage` dijalankan:
1. Muncul dialog "Allow Termux to access photos..." → Klik **Allow**
2. Buka **Pengaturan Android** → Aplikasi → Termux → Izin → aktifkan semua
3. Buka **Pengaturan Android** → Aplikasi → Termux:API → Izin → aktifkan semua
4. Aktifkan "Tampilkan di atas aplikasi lain" untuk Termux:API (untuk screenshot)

### Langkah 4 — Jalankan

**Terminal 1** — Jalankan AI Server:
```bash
cd ~/termux-ai-assistant
bash start-server.sh
```

Tunggu hingga muncul:
```
llama server listening at http://127.0.0.1:8080
```
(sekitar 10-30 detik tergantung model)

**Terminal 2** — Buka sesi baru di Termux (swipe kiri → New Session):
```bash
cd ~/termux-ai-assistant
bash start-ai.sh
```

---

## Cara Pakai

### Chat dengan AI

```
> Halo, siapa kamu?
> /chat Jelaskan cara kerja async/await di Python
```

### Screenshot

```
> /screenshot
> /screenshots          ← lihat daftar
> /share-ss /path/file  ← share via Android
```

### Rekam Layar

```
> /record 60            ← rekam 60 detik
> /record-stop          ← hentikan
> /recordings           ← lihat daftar
```

### Coding Assistant

```
> /code Buatkan REST API dengan FastAPI untuk manajemen todo
> /debug ~/project/main.py
> /review ~/project/api.py
> /ask ~/project/app.js Apa yang dilakukan fungsi fetchData?
```

### Kelola File

```
> /ls ~/storage/shared/Download
> /read ~/project/config.json
> /tree ~/myproject
> /scan ~/myproject
> /zip ~/backup.zip ~/myproject
```

### Edit Kode

```
> /edit ~/project/main.py
  (masukkan teks lama yang ingin diganti, akhiri dengan EOF)
  (masukkan teks baru, akhiri dengan EOF)

> /new ~/project/utils.py
  (ketik isi file, akhiri dengan EOF)
```

---

## Struktur Folder

```
termux-ai-assistant/
├── main.py              ← Program utama (jalankan ini)
├── ai_client.py         ← Client AI (llama.cpp / Ollama)
├── screen_capture.py    ← Modul screenshot
├── screen_record.py     ← Modul rekam layar
├── file_sender.py       ← Manajemen file
├── project_editor.py    ← Editor kode & project
├── config.py            ← Konfigurasi
├── requirements.txt     ← Dependensi Python
├── install.sh           ← Script instalasi otomatis
├── start-server.sh      ← Jalankan llama.cpp server
├── start-ai.sh          ← Jalankan AI assistant
├── models/              ← Folder model AI (.gguf)
│   └── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
├── llama_build/         ← Source llama.cpp (setelah kompilasi)
├── llama-server         ← Binary llama-server (setelah kompilasi)
└── temp/                ← File sementara
```

---

## Ganti Model AI

### Gunakan model lain (tanpa API key)

```bash
# Download Qwen2.5-0.5B (lebih ringan ~400MB)
wget -O models/qwen.gguf \
  "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"

# Restart server dengan model baru
./llama-server -m models/qwen.gguf --host 127.0.0.1 --port 8080
```

### Gunakan Ollama (alternatif)

```bash
# Install Ollama untuk ARM (jika tersedia)
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull tinyllama

# Ubah backend di assistant
> /backend ollama
```

---

## Troubleshooting

| Masalah | Solusi |
|---|---|
| `termux-screenshot tidak ditemukan` | `pkg install termux-api` + install Termux:API dari F-Droid |
| `Tidak bisa connect ke llama.cpp` | Jalankan `bash start-server.sh` dulu di terminal lain |
| `Download model gagal` | Gunakan WiFi, atau download manual di browser lalu pindah ke folder `models/` |
| `Kompilasi llama.cpp gagal` | Jalankan `pkg install clang cmake make` lalu ulangi |
| `Storage tidak bisa diakses` | Jalankan `termux-setup-storage` lalu Allow |
| Model terlalu lambat | Gunakan Qwen2.5-0.5B (lebih ringan) atau turunkan `-c 1024` di start-server.sh |

---

## Izin yang Dibutuhkan

| Izin | Kegunaan |
|---|---|
| Storage (Read/Write) | Akses file, simpan screenshot/rekaman |
| Termux:API | Screenshot, share file, buka file |
| Display over apps | Screenshot via Termux:API |

> **Catatan:** Screen recording via `screenrecord` mungkin memerlukan root di beberapa perangkat. Alternatifnya gunakan `termux-screen-record` dari Termux:API.

---

## Keterbatasan

- Screen recording tanpa root terbatas di beberapa ROM Android (MIUI, One UI, ColorOS)
- Model AI lokal lebih lambat dari cloud AI tapi 100% privat
- Kualitas respons TinyLlama lebih terbatas dari GPT-4, tapi cukup untuk coding
- Tidak ada akses kamera (hanya screenshot layar)

---

## Ganti Backend AI

Backend bisa diganti kapan saja tanpa restart program:

```
> /backend llamacpp    ← gunakan llama.cpp lokal
> /backend ollama      ← gunakan Ollama lokal
```

Atau edit `config.py`:
```python
AI_BACKEND = "llamacpp"   # atau "ollama"
```

---

*Dibuat untuk Oppo A92 — berjalan offline, gratis, tanpa API key.*
