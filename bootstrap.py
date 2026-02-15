import sys
import subprocess
import importlib
from pathlib import Path
import urllib.request
import zipfile
import shutil
import os



BASE_DIR = Path(__file__).resolve().parent
SETTINGS_DIR = BASE_DIR / "settings"

MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_PATH = BASE_DIR / MODEL_NAME



REQUIRED_PACKAGES = [
    "vosk",
    "sounddevice",
    "edge-tts",
    "soundfile",
    "serpapi",
    "pyautogui",
    "flet",
    "httpx",
    "google-search-results",
    "Pillow",
    "requests",
]


def check_python():
    if sys.version_info < (3, 10):
        print("Python 3.10+ is required.")
        sys.exit(1)


def install_package(package):
    print(f"Installing {package}...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", package]
    )


def ensure_packages():
    print("Checking dependencies...")

    for package in REQUIRED_PACKAGES:
        module_name = package.replace("-", "_")
        try:
            importlib.import_module(module_name)
        except ImportError:
            install_package(package)

    print("All dependencies ready.")


def download_model():
    zip_path = BASE_DIR / f"{MODEL_NAME}.zip"

    print("\nVosk model not found.")
    print("Downloading model (this may take 1–3 minutes)...")

    try:
        urllib.request.urlretrieve(MODEL_URL, zip_path)
    except Exception as e:
        print("Download failed:", e)
        sys.exit(1)

    print("Extracting model...")

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(BASE_DIR)
    except Exception as e:
        print("Extraction failed:", e)
        sys.exit(1)
    finally:
        zip_path.unlink(missing_ok=True)

    if not MODEL_PATH.exists():
        for folder in BASE_DIR.iterdir():
            if folder.is_dir() and MODEL_NAME in folder.name:
                shutil.move(str(folder), str(MODEL_PATH))
                break

    if not MODEL_PATH.exists():
        print("Model extraction failed. Folder not found.")
        sys.exit(1)

    print("Model ready.\n")


def ensure_model():
    if MODEL_PATH.exists():
        print("Vosk model detected.")
        return

    download_model()


def ensure_settings():
    SETTINGS_DIR.mkdir(exist_ok=True)


def bootstrap():
    print("Starting AERIS first-run setup...\n")

    check_python()
    ensure_packages()
    ensure_model()
    ensure_settings()

    print("AERIS setup complete.\n")
