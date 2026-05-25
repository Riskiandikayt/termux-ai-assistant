import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.expanduser("~/storage/shared")
SCREENSHOTS_DIR = os.path.join(STORAGE_DIR, "Pictures", "AIAssistant", "screenshots")
RECORDINGS_DIR = os.path.join(STORAGE_DIR, "Movies", "AIAssistant", "recordings")
DOWNLOADS_DIR = os.path.join(STORAGE_DIR, "Download", "AIAssistant")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

for d in [SCREENSHOTS_DIR, RECORDINGS_DIR, DOWNLOADS_DIR, TEMP_DIR]:
    os.makedirs(d, exist_ok=True)

AI_BACKEND = os.environ.get("AI_BACKEND", "llamacpp")

LLAMACPP_HOST = os.environ.get("LLAMACPP_HOST", "http://127.0.0.1:8080")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "tinyllama")

DEFAULT_MODEL_PATH = os.path.join(BASE_DIR, "models", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")

MAX_TOKENS = 2048
TEMPERATURE = 0.7
STREAM = True

SCREEN_RECORD_DEFAULT_DURATION = 30
SCREEN_RECORD_MAX_DURATION = 180
SCREEN_RECORD_BIT_RATE = "2M"
SCREEN_RECORD_SIZE = "1280x720"
