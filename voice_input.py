import sounddevice as sd
import vosk
import queue
import sys
import json
import threading
from pathlib import Path
import time
import os


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()

MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_PATH = BASE_DIR / MODEL_NAME



if not MODEL_PATH.exists():
    raise RuntimeError(
        "ERROR: Vosk model not found.\n"
        "Bootstrap should have installed it."
    )

print("Loading Vosk model...")
model = vosk.Model(str(MODEL_PATH))


q = queue.Queue()
stop_listening_flag = threading.Event()


def callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))


 # Due to the inaccurate voice model when hearing wake words, wake aliases function so that AI can recognize similar words.
 # For example, "aeris" can be misheard as "aries", "air is", "iris", "arrow", "harris", "heiress", "errors", "the heiress", "eras", etc.
 # Feel free to add more aliases to improve wake word recognition accuracy.
WAKE_ALIASES = [
    "aeris",
    "aries",
    "air is",
    "eris",
    "iris",
    "arrow",
    "harris",
    "heiress",
    "errors",
    "the heiress",
    "eras"
]


def listen_for_wake_word(wake_word="aeris", timeout=None):
    print(f"Click the orb to start or say '{wake_word}' to wake up Aeris...")

    rec = vosk.KaldiRecognizer(model, 16000)
    start_time = time.time()

    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype='int16',
        channels=1,
        callback=callback
    ):
        while not stop_listening_flag.is_set():

            if timeout and (time.time() - start_time) > timeout:
                return False

            try:
                data = q.get(timeout=0.1)
            except queue.Empty:
                continue

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").lower()

                if not text:
                    continue


                if any(alias in text for alias in WAKE_ALIASES):
                    print("Wake word detected!")
                    return True

    return False


def record_voice(prompt="Listening for command..."):
    print(prompt)

    rec = vosk.KaldiRecognizer(model, 16000)

    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype='int16',
        channels=1,
        callback=callback
    ):
        while not stop_listening_flag.is_set():

            try:
                data = q.get(timeout=0.1)
            except queue.Empty:
                continue

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").strip()

                if text:
                    print("You:", text)
                    return text

    return ""
