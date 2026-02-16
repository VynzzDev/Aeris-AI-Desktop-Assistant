import sys
import subprocess
import importlib
from pathlib import Path
import urllib.request
import zipfile
import shutil
import os
import time



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



def progress_bar(current, total, prefix=""):
    bar_length = 40
    percent = current / total
    filled = int(bar_length * percent)
    bar = "█" * filled + "-" * (bar_length - filled)
    print(f"\r{prefix} |{bar}| {percent*100:5.1f}%", end="", flush=True)


def check_python():
    if sys.version_info < (3, 10):
        print("Python 3.10+ is required.")
        sys.exit(1)



def install_package(package):
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", package],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def ensure_packages():
    print("Checking dependencies...\n")

    total = len(REQUIRED_PACKAGES)
    installed = 0

    for i, package in enumerate(REQUIRED_PACKAGES, start=1):
        module_name = package.replace("-", "_")
        try:
            importlib.import_module(module_name)
        except ImportError:
            install_package(package)

        installed += 1
        progress_bar(installed, total, prefix="Dependencies")

    print("\nAll dependencies ready.\n")



def download_with_progress(url, destination):

    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            progress_bar(downloaded, total_size, prefix="Downloading model")

    urllib.request.urlretrieve(url, destination, reporthook)



def download_model():
    zip_path = BASE_DIR / f"{MODEL_NAME}.zip"

    print("Vosk model not found.\n")

    try:
        download_with_progress(MODEL_URL, zip_path)
    except Exception as e:
        print("\nDownload failed:", e)
        sys.exit(1)

    print("\nExtracting model...")

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            members = zip_ref.namelist()
            total = len(members)

            for i, member in enumerate(members, start=1):
                zip_ref.extract(member, BASE_DIR)
                progress_bar(i, total, prefix="Extracting")
    except Exception as e:
        print("\nExtraction failed:", e)
        sys.exit(1)
    finally:
        zip_path.unlink(missing_ok=True)

    if not MODEL_PATH.exists():
        for folder in BASE_DIR.iterdir():
            if folder.is_dir() and MODEL_NAME in folder.name:
                shutil.move(str(folder), str(MODEL_PATH))
                break

    if not MODEL_PATH.exists():
        print("\nModel extraction failed.")
        sys.exit(1)

    print("\nModel ready.\n")



def ensure_model():
    if MODEL_PATH.exists():
        print("Vosk model detected.\n")
        return

    download_model()



def ensure_settings():
    SETTINGS_DIR.mkdir(exist_ok=True)



def bootstrap():
    print("\n==============================")
    print("       AERIS BOOTSTRAP")
    print("==============================\n")

    check_python()

    steps = 4
    current_step = 0

    current_step += 1
    print(f"[{current_step}/{steps}] Installing dependencies")
    ensure_packages()

    current_step += 1
    print(f"[{current_step}/{steps}] Checking voice model")
    ensure_model()

    current_step += 1
    print(f"[{current_step}/{steps}] Preparing settings folder")
    ensure_settings()

    current_step += 1
    print(f"[{current_step}/{steps}] Finalizing setup")
    time.sleep(0.5)

    print("\nAERIS setup complete.\n")
