import re
import asyncio
from datetime import datetime, timedelta
import threading

try:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
except:
    toaster = None


class AlarmManager:

    def __init__(self):
        self.alarms = []

    def parse_time(self, text: str):
        text = text.lower()

        match_in = re.search(r"in (\d+)\s*(minute|minutes|hour|hours)", text)
        if match_in:
            value = int(match_in.group(1))
            unit = match_in.group(2)

            if "hour" in unit:
                return datetime.now() + timedelta(hours=value)
            else:
                return datetime.now() + timedelta(minutes=value)

        match_at = re.search(r"(?:at )?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
        if match_at:
            hour = int(match_at.group(1))
            minute = int(match_at.group(2) or 0)
            meridiem = match_at.group(3)

            if meridiem:
                if meridiem == "pm" and hour != 12:
                    hour += 12
                if meridiem == "am" and hour == 12:
                    hour = 0

            now = datetime.now()
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            if target < now:
                target += timedelta(days=1)

            return target

        return None

    def _notify(self, message):
        if toaster:
            try:
                toaster.show_toast(
                    "AERIS Alarm",
                    message,
                    duration=10,
                    threaded=True
                )
            except:
                pass

    async def _alarm_task(self, ui, target_time, speak_function):

        delay = (target_time - datetime.now()).total_seconds()
        if delay <= 0:
            return

        await asyncio.sleep(delay)

        message = "Sir, your alarm is ringing."

        ui.write_log(f"AI: {message}")

        threading.Thread(
            target=self._notify,
            args=(message,),
            daemon=True
        ).start()

        speak_function(ui, message)

    def create_alarm(self, ui, user_text, speak_function):

        target_time = self.parse_time(user_text)

        if not target_time:
            return "Sir, I could not determine the alarm time."

        asyncio.create_task(
            self._alarm_task(ui, target_time, speak_function)
        )

        return f"Alarm set for {target_time.strftime('%H:%M')}, sir."