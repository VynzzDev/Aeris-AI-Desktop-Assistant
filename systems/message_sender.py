import time
import pyautogui

REQUIRED_PARAMS = ["receiver", "message_text", "platform"]


def send_message(
    parameters: dict,
    response: str | None = None,
    player=None,
    session_memory=None
) -> str | None:
    """
    Send a message via Windows app (WhatsApp, Telegram, etc.)

    Multi-step support using session_memory.

    Returns:
        - String to be spoken
        - None if waiting for next user input
    """

    if session_memory is None:
        return "Session memory missing, cannot proceed."

    if parameters:
        session_memory.update_parameters(parameters)

    for param in REQUIRED_PARAMS:
        value = session_memory.get_parameter(param)
        if not value:
            session_memory.set_current_question(param)

            if param == "receiver":
                return "Sir, who should I send the message to?"

            elif param == "message_text":
                return "Sir, what should I say?"

            elif param == "platform":
                return "Sir, which platform should I use? (WhatsApp, Telegram, etc.)"

            else:
                return f"Sir, please provide {param}."

    receiver = session_memory.get_parameter("receiver").strip()
    platform = session_memory.get_parameter("platform").strip() or "WhatsApp"
    message_text = session_memory.get_parameter("message_text").strip()

    try:
        pyautogui.PAUSE = 0.1

        pyautogui.press("win")
        time.sleep(0.3)
        pyautogui.write(platform, interval=0.03)
        pyautogui.press("enter")
        time.sleep(0.6)

        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.2)
        pyautogui.write(receiver, interval=0.03)
        time.sleep(0.2)
        pyautogui.press("enter")
        time.sleep(0.2)

        pyautogui.write(message_text, interval=0.03)
        pyautogui.press("enter")

        session_memory.clear_current_question()
        session_memory.clear_pending_intent()
        session_memory.update_parameters({})

        return f"Sir, message sent to {receiver} via {platform}."

    except Exception:
        return f"Sir, I failed to send the message to {receiver}."
