import asyncio
import threading

from bootstrap import bootstrap
bootstrap()

from voice_input import record_voice, listen_for_wake_word, stop_listening_flag
from brain import get_llm_output
from tts import edge_speak, stop_speaking
from interface import AerisUI

from systems.launch_app import open_app
from systems.internet_search import web_search
from systems.weather_info import weather_action
from systems.alarm_system import AlarmManager
from systems.message_sender import send_message
from systems.aircraft_report import handle_aircraft_command

from memory.memory_manager import load_memory, update_memory
from memory.temporary_memory import TemporaryMemory


interrupt_commands = ["mute", "quit", "exit", "stop"]
temp_memory = TemporaryMemory()
alarm_manager = AlarmManager()

MAIN_LOOP = None


async def get_voice_input():
    return await asyncio.to_thread(record_voice)


def speak_with_state(ui: AerisUI, response: str):
    try:
        edge_speak(response, ui)
    except Exception as e:
        print("Speak error:", e)


async def process_user_input(ui: AerisUI, user_text: str, use_tts: bool):

    if not user_text:
        return

    lower_text = user_text.lower()

    if any(cmd in lower_text for cmd in interrupt_commands):
        stop_speaking()
        temp_memory.reset()
        ui.stop_speaking()
        ui.stop_processing()
        return

    ui.start_processing()

    alarm_keywords = ["set alarm", "wake me up", "alarm at", "alarm in"]

    if any(k in lower_text for k in alarm_keywords):

        result = alarm_manager.create_alarm(
            ui,
            user_text,
            speak_with_state
        )

        if result:
            ui.write_log(f"AI: {result}")
            if use_tts:
                speak_with_state(ui, result)
            else:
                ui.stop_processing()

        return

    try:
        aircraft_response = handle_aircraft_command(user_text)
        if aircraft_response:
            ui.write_log(f"AI: {aircraft_response}")
            if use_tts:
                speak_with_state(ui, aircraft_response)
            else:
                ui.stop_processing()
            return
    except Exception as e:
        error_msg = f"Aircraft system error: {e}"
        ui.write_log(f"AI: {error_msg}")
        if use_tts:
            speak_with_state(ui, error_msg)
        else:
            ui.stop_processing()
        return

    long_term_memory = load_memory()
    memory_for_prompt = {}

    identity = long_term_memory.get("identity", {})
    if "name" in identity:
        memory_for_prompt["user_name"] = identity["name"].get("value")

    history_lines = temp_memory.get_history_for_prompt()
    if history_lines:
        memory_for_prompt["recent_conversation"] = history_lines

    try:
        llm_output = await asyncio.to_thread(
            get_llm_output,
            user_text,
            memory_for_prompt
        )
    except Exception as e:
        error_msg = f"AI error: {e}"
        ui.write_log(f"AI: {error_msg}")
        if use_tts:
            speak_with_state(ui, error_msg)
        else:
            ui.stop_processing()
        return

    intent = llm_output.get("intent", "chat")
    parameters = llm_output.get("parameters") or {}
    response = llm_output.get("text") or ""
    memory_update = llm_output.get("memory_update")

    if memory_update and isinstance(memory_update, dict):
        update_memory(memory_update)

    temp_memory.set_last_ai_response(response)

    final_text = None

    if intent == "open_app":
        open_app(
            parameters=parameters,
            response=response,
            player=ui,
            session_memory=temp_memory
        )
        final_text = response or f"Opening {parameters.get('app_name','application')}."

    elif intent == "weather_report":
        final_text = weather_action(
            parameters=parameters,
            player=ui,
            session_memory=temp_memory
        )

    elif intent == "search":
        final_text = web_search(
            parameters=parameters,
            player=ui,
            session_memory=temp_memory
        )

    elif intent == "send_message":
        send_message(
            parameters=parameters,
            player=ui,
            session_memory=temp_memory
        )
        final_text = response or "Message sent."

    else:
        final_text = response

    if final_text and final_text.strip():
        ui.write_log(f"AI: {final_text}")
        if use_tts:
            speak_with_state(ui, final_text)
        else:
            ui.stop_processing()
    else:
        ui.write_log("AI: Done.")
        ui.stop_processing()


async def ai_loop(ui: AerisUI):

    global MAIN_LOOP
    MAIN_LOOP = asyncio.get_running_loop()
    ui.set_backend_loop(MAIN_LOOP)

    while True:

        stop_listening_flag.clear()

        wake_task = asyncio.create_task(
            asyncio.to_thread(listen_for_wake_word, "aeris")
        )

        push_task = asyncio.create_task(
            asyncio.to_thread(ui.push_to_talk_event.wait)
        )

        done, pending = await asyncio.wait(
            [wake_task, push_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

        if ui.push_to_talk_event.is_set():
            ui.push_to_talk_event.clear()
            stop_listening_flag.set()
            await asyncio.sleep(0.1)
            stop_listening_flag.clear()

        ui.start_listening()

        stop_listening_flag.clear()

        user_text = await get_voice_input()

        ui.stop_listening()

        await process_user_input(ui, user_text, use_tts=True)

        await asyncio.sleep(0.05)


def main():

    ui = AerisUI(size=(1000, 720))

    def runner():
        asyncio.run(ai_loop(ui))

    threading.Thread(target=runner, daemon=True).start()

    ui.run()


if __name__ == "__main__":
    main()
