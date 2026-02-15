import io
import asyncio
import threading
import sounddevice as sd
import soundfile as sf
import edge_tts


VOICE = "en-US-MichelleNeural"

RATE = "+0%"
VOLUME = "+0%"
PITCH = "+0Hz"

stop_speaking_flag = threading.Event()


def edge_speak(text: str, ui=None):
    """
    Fully blocking TTS.
    UI speaking state is synchronized
    exactly when audio playback starts.
    """

    if not text or not text.strip():
        return

    stop_speaking_flag.clear()
    finished_event = threading.Event()

    def runner():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_speak_async(text.strip(), ui))
            loop.close()
        except Exception as e:
            print("EDGE TTS ERROR:", e)
        finally:
            finished_event.set()

    threading.Thread(target=runner, daemon=True).start()

    finished_event.wait()



async def _speak_async(text: str, ui=None):

    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate=RATE,
        volume=VOLUME,
        pitch=PITCH,
    )

    audio_bytes = io.BytesIO()

    async for chunk in communicate.stream():
        if stop_speaking_flag.is_set():
            return

        if chunk["type"] == "audio":
            audio_bytes.write(chunk["data"])

    audio_bytes.seek(0)

    data, samplerate = sf.read(audio_bytes, dtype="float32")
    channels = data.shape[1] if len(data.shape) > 1 else 1

    if ui:
        ui.stop_processing()
        ui.start_speaking()

    try:
        with sd.OutputStream(
            samplerate=samplerate,
            channels=channels,
            dtype="float32",
        ) as stream:

            block_size = 1024

            for start in range(0, len(data), block_size):
                if stop_speaking_flag.is_set():
                    break

                stream.write(data[start:start + block_size])

    finally:
        if ui:
            ui.stop_speaking()


def stop_speaking():
    stop_speaking_flag.set()
