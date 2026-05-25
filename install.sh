#!/data/data/com.termux/files/usr/bin/bash
# =========================================================
# Install Script — AI Assistant Termux
# Oppo A92 / Android 11+
# =========================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'; BOLD='\033[1m'

echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════╗"
echo "║    Install AI Assistant untuk Termux     ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Update paket ───────────────────────────────────────
echo -e "${YELLOW}[1/8] Update paket Termux...${NC}"
pkg update -y && pkg upgrade -y

# ── 2. Install dependensi sistem ──────────────────────────
echo -e "${YELLOW}[2/8] Install Python, wget, git, ffmpeg...${NC}"
pkg install -y python wget curl git clang make cmake ffmpeg termux-api

# ── 3. Izin storage ───────────────────────────────────────
echo -e "${YELLOW}[3/8] Meminta izin akses storage...${NC}"
termux-setup-storage
echo -e "${GREEN}✅  Izin storage diminta. Klik 'Allow' di dialog Android.${NC}"
sleep 3

# ── 4. Install Python dependencies ────────────────────────
echo -e "${YELLOW}[4/8] Install Python packages...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# ── 5. Kompilasi llama.cpp ────────────────────────────────
echo -e "${YELLOW}[5/8] Kompilasi llama.cpp (bisa 5-10 menit)...${NC}"
mkdir -p llama_build
cd llama_build

if [ ! -d "llama.cpp" ]; then
    git clone --depth=1 https://github.com/ggerganov/llama.cpp.git
fi
cd llama.cpp

mkdir -p build && cd build

# ARM64 optimized (Snapdragon 665)
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DGGML_OPENMP=OFF \
    -DGGML_NATIVE=OFF \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_BUILD_EXAMPLES=ON 2>&1 | tail -5

cmake --build . --config Release -j$(nproc) 2>&1 | tail -10

cd ../../..

# Salin binary ke root project
LLAMA_BIN="llama_build/llama.cpp/build/bin"
if [ -f "$LLAMA_BIN/llama-server" ]; then
    cp "$LLAMA_BIN/llama-server" ./llama-server
    chmod +x ./llama-server
    echo -e "${GREEN}✅  llama-server berhasil dikompilasi!${NC}"
elif [ -f "$LLAMA_BIN/server" ]; then
    cp "$LLAMA_BIN/server" ./llama-server
    chmod +x ./llama-server
    echo -e "${GREEN}✅  llama-server berhasil dikompilasi!${NC}"
else
    echo -e "${RED}⚠️   Kompilasi llama-server tidak ditemukan. Coba kompilasi manual.${NC}"
fi

# ── 6. Download model TinyLlama ───────────────────────────
echo -e "${YELLOW}[6/8] Download model TinyLlama 1.1B Q4_K_M (~670MB)...${NC}"
mkdir -p models

MODEL_URL="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
MODEL_PATH="models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

if [ -f "$MODEL_PATH" ]; then
    echo -e "${GREEN}✅  Model sudah ada, skip download.${NC}"
else
    echo "Download sedang berjalan... (670MB, sabar ya)"
    wget -c --show-progress -O "$MODEL_PATH" "$MODEL_URL" || {
        echo -e "${RED}❌  Download gagal. Coba manual:${NC}"
        echo "  wget -c -O models/tinyllama.gguf '$MODEL_URL'"
    }
fi

# ── 7. Buat folder temp & data ────────────────────────────
echo -e "${YELLOW}[7/8] Membuat folder kerja...${NC}"
mkdir -p temp
mkdir -p ~/storage/shared/Pictures/AIAssistant/screenshots 2>/dev/null || true
mkdir -p ~/storage/shared/Movies/AIAssistant/recordings 2>/dev/null || true
mkdir -p ~/storage/shared/Download/AIAssistant 2>/dev/null || true

# ── 8. Buat launcher script ───────────────────────────────
echo -e "${YELLOW}[8/8] Membuat launcher script...${NC}"

cat > start-server.sh << 'SERVERSCRIPT'
#!/data/data/com.termux/files/usr/bin/bash
# Jalankan llama-server di background
MODEL=$(ls models/*.gguf 2>/dev/null | head -1)
if [ -z "$MODEL" ]; then
    echo "❌ Tidak ada model .gguf di folder models/"
    exit 1
fi
echo "🚀 Menjalankan llama.cpp server dengan model: $MODEL"
./llama-server \
    -m "$MODEL" \
    --host 127.0.0.1 \
    --port 8080 \
    -c 2048 \
    -n 512 \
    --threads $(nproc) \
    --no-mmap 2>&1 &

SERVER_PID=$!
echo "✅ Server berjalan (PID $SERVER_PID) di http://127.0.0.1:8080"
echo "   Tunggu 10-30 detik sampai model dimuat..."
echo "   Hentikan dengan: kill $SERVER_PID"
SERVERSCRIPT

cat > start-ai.sh << 'AISCRIPT'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")"
python main.py
AISCRIPT

chmod +x start-server.sh start-ai.sh

# ── Selesai ───────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║  ✅  INSTALASI SELESAI!                    ║${NC}"
echo -e "${GREEN}${BOLD}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}LANGKAH SELANJUTNYA:${NC}"
echo ""
echo -e "  ${YELLOW}Terminal 1${NC} — Jalankan AI server:"
echo "    bash start-server.sh"
echo ""
echo -e "  ${YELLOW}Terminal 2${NC} — Jalankan AI assistant:"
echo "    bash start-ai.sh"
echo ""
echo -e "${CYAN}TIPS:${NC}"
echo "  • Buka 2 sesi Termux (swipe kiri di Termux untuk tambah sesi)"
echo "  • Tunggu 10-30 detik setelah start-server sebelum chat"
echo "  • Ketik /help di dalam assistant untuk daftar perintah"
echo ""
echo -e "${YELLOW}IZIN ANDROID YANG PERLU DIAKTIFKAN:${NC}"
echo "  • Storage   → Pengaturan > Aplikasi > Termux > Izin > Storage"
echo "  • Termux:API → Install dari F-Droid, beri izin yang diminta"
echo ""
