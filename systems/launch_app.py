import time
import pyautogui


def open_app(
    parameters: dict,
    response: str | None = None,
    player=None,
    session_memory=None
) -> str | None:
    """
    Opens an application using Windows search.

    Returns:
        - String message (for TTS + UI)
        - None if something failed silently
    """

    app_name = (parameters or {}).get("app_name", "").strip()

    if not app_name and session_memory:
        app_name = getattr(session_memory, "open_app", "") or ""

    if not app_name:
        return "Sir, I couldn't determine which application to open."

    try:
        pyautogui.PAUSE = 0.1

        pyautogui.press("win")
        time.sleep(0.3)

        pyautogui.write(app_name, interval=0.03)
        time.sleep(0.2)

        pyautogui.press("enter")
        time.sleep(0.6)

        if session_memory:
            session_memory.set_open_app(app_name)

        if response:
            return response

        return f"Opening {app_name}, sir."

    except Exception:
        return f"Sir, I failed to open {app_name}."
