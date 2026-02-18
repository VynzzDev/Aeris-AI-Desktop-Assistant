import flet as ft
import asyncio
import math
import time
import os
import json
import threading
from pathlib import Path
import sys


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
CONFIG_DIR = BASE_DIR / "settings"
API_FILE = CONFIG_DIR / "keys.json"


class AerisUI:
    def __init__(self, size=(1000, 720)):
        self.size = size
        self._page = None
        self._mode = "live"
        self._state = "idle"

        self._audio_level = 0.0
        self._smoothed_audio = 0.0

        self._start_time = time.perf_counter()
        self._current_scale = 1.0
        self._orb_base = 170

        self._running = True

        self.push_to_talk_event = threading.Event()
        self.backend_loop = None
        self._chat_loading_ref = None


    def set_backend_loop(self, loop):
        self.backend_loop = loop


    def _safe_ui(self, fn):
        if not self._page:
            return
        try:
            self._page.run_threadsafe(fn)
        except:
            try:
                fn()
            except:
                pass


    async def _main(self, page: ft.Page):
        self._page = page
        page.title = "AERIS AI Assistant"
        page.window_width = self.size[0]
        page.window_height = self.size[1]
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = "#0b0f19"

        if not API_FILE.exists():
            self._show_setup()
        else:
            self._build_main_ui()

        page.update()


    def _show_setup(self):

        self._success_icon = ft.Icon(
            ft.Icons.CHECK_CIRCLE,
            size=90,
            color="#22c55e",
            opacity=0,
        )

        self._openrouter_input = ft.TextField(
            label="OpenRouter API Key",
            password=True,
            filled=True,
            bgcolor="#111827",
            border_radius=16,
        )

        self._serpapi_input = ft.TextField(
            label="SerpAPI Key",
            password=True,
            filled=True,
            bgcolor="#111827",
            border_radius=16,
        )

        self._save_btn = ft.ElevatedButton(
            "Initialize AERIS",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=18),
                bgcolor="#2563eb",
                padding=20,
            ),
            on_click=self._save_api_keys,
        )

        setup_card = ft.Container(
            width=480,
            padding=40,
            border_radius=24,
            bgcolor="#0f172a",
            shadow=ft.BoxShadow(
                blur_radius=50,
                spread_radius=1,
                color="#00000088",
            ),
            content=ft.Column(
                [
                    ft.Text("Welcome to AERIS",
                            size=26,
                            weight=ft.FontWeight.W_600),
                    ft.Text("Enter your API credentials to begin.",
                            size=14,
                            color="#94a3b8"),
                    ft.Container(height=25),
                    self._openrouter_input,
                    self._serpapi_input,
                    ft.Container(height=25),
                    self._save_btn,
                    ft.Container(height=25),
                    self._success_icon,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
        )

        background = ft.Container(
            expand=True,
            gradient=ft.RadialGradient(
                center=ft.Alignment(0, 0),
                radius=1.2,
                colors=["#0f1c3d", "#0b0f19"],
            ),
            content=ft.Row(
                [setup_card],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        self._page.add(background)


    async def _success_animation(self):

        self._save_btn.disabled = True
        self._success_icon.opacity = 1
        self._page.update()

        for i in range(15):
            self._success_icon.scale = 1 + (i * 0.02)
            self._page.update()
            await asyncio.sleep(0.02)

        await asyncio.sleep(0.6)

        self._page.controls.clear()
        self._build_main_ui()
        self._page.update()


    def _save_api_keys(self, e):

        openrouter_key = self._openrouter_input.value.strip()
        serpapi_key = self._serpapi_input.value.strip()

        if not openrouter_key:
            return

        os.makedirs(CONFIG_DIR, exist_ok=True)

        with open(API_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "openrouter_api_key": openrouter_key,
                    "serpapi_api_key": serpapi_key,
                },
                f,
                indent=4,
            )

        asyncio.create_task(self._success_animation())


    def _build_main_ui(self):

        self._background = ft.Container(
            expand=True,
            gradient=ft.RadialGradient(
                center=ft.Alignment(0, 0),
                radius=1.0,
                colors=["#0f1c3d", "#0b0f19"],
            ),
        )

        root = ft.Stack(
            [
                self._background,
                self._build_live(),
                self._build_chat(),
            ],
            expand=True,
        )

        self._page.add(root)
        asyncio.create_task(self._animation_loop())


    def _build_live(self):

        self._core = ft.Container(
            width=self._orb_base,
            height=self._orb_base,
            border_radius=self._orb_base // 2,
            gradient=ft.RadialGradient(
                colors=["#38bdf8", "#2563eb"],
            ),
            shadow=ft.BoxShadow(
                blur_radius=60,
                spread_radius=1,
                color="#2563eb55",
            ),
        )

        self._glow = ft.Container(
            width=self._orb_base + 200,
            height=self._orb_base + 200,
            border_radius=(self._orb_base + 200) // 2,
            gradient=ft.RadialGradient(
                colors=["#2563eb33", "#00000000"],
            ),
        )

        orb_button = ft.GestureDetector(
            content=ft.Stack(
                [
                    ft.Row([self._glow], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self._core], alignment=ft.MainAxisAlignment.CENTER),
                ]
            ),
            on_tap=self._on_push_to_talk,
        )

        self._status = ft.Text(
            "Idle",
            size=16,
            weight=ft.FontWeight.W_500,
            color="#94a3b8",
        )

        toggle = self._modern_icon_button(
            ft.Icons.CHAT_BUBBLE_OUTLINE,
            lambda e: self._switch("chat"),
        )

        header = ft.Row(
            [
                ft.Text("A.E.R.I.S", size=18, weight=ft.FontWeight.W_600),
                ft.Container(expand=True),
                toggle,
            ]
        )

        self._live_view = ft.Container(
            visible=True,
            padding=40,
            content=ft.Column(
                [
                    header,
                    ft.Container(expand=True),
                    orb_button,
                    ft.Container(height=30),
                    self._status,
                    ft.Container(expand=True),
                ],
                expand=True,
            ),
        )

        return self._live_view


    def _on_push_to_talk(self, e):
        from voice_input import stop_listening_flag

        if self._state == "listening":
            stop_listening_flag.set()
            self.stop_listening()
            return

        self.push_to_talk_event.set()


    def _build_chat(self):

        self._chat_list = ft.ListView(
            expand=True,
            spacing=14,
            padding=25,
            auto_scroll=True,
        )

        self._input = ft.TextField(
            hint_text="Message...",
            expand=True,
            filled=True,
            bgcolor="#161b2e",
            border_color="transparent",
            border_radius=18,
            on_submit=self._send_message,
        )

        send_btn = self._modern_icon_button(
            ft.Icons.SEND_ROUNDED,
            self._send_message,
        )

        toggle = self._modern_icon_button(
            ft.Icons.MIC,
            lambda e: self._switch("live"),
        )

        header = ft.Row(
            [
                ft.Text("A.E.R.I.S", size=18, weight=ft.FontWeight.W_600),
                ft.Container(expand=True),
                toggle,
            ]
        )

        self._chat_view = ft.Container(
            visible=False,
            padding=30,
            content=ft.Column(
                [
                    header,
                    self._chat_list,
                    ft.Row([self._input, send_btn]),
                ],
                expand=True,
            ),
        )

        return self._chat_view


    def show_chat_loading(self):
        if self._mode != "chat":
            return

        loading = self._bubble("Thinking...", user=False)
        self._chat_loading_ref = loading
        self._safe_ui(lambda: self._chat_list.controls.append(loading))
        self._safe_ui(self._page.update)


    def remove_chat_loading(self):
        if self._chat_loading_ref:
            try:
                self._safe_ui(lambda: self._chat_list.controls.remove(self._chat_loading_ref))
            except:
                pass
            self._chat_loading_ref = None
            self._safe_ui(self._page.update)


    def append_ai_typing(self, full_text: str, speed: float = 0.02):

        if self._mode != "chat":
            return

        async def typing_animation():

            self.remove_chat_loading()

            bubble = self._bubble("", user=False)

            self._safe_ui(lambda: self._chat_list.controls.append(bubble))
            self._safe_ui(self._page.update)

            text_control = bubble.controls[0].content
            current_text = ""

            for char in full_text:
                current_text += char

                def update():
                    text_control.value = current_text
                    self._page.update()

                self._safe_ui(update)
                await asyncio.sleep(speed)

        if self.backend_loop:
            asyncio.run_coroutine_threadsafe(
                typing_animation(),
                self.backend_loop
            )


    def _send_message(self, e):

        text = self._input.value.strip()
        if not text:
            return

        self._chat_list.controls.append(self._bubble(text, user=True))
        self._input.value = ""
        self._page.update()

        self.show_chat_loading()

        if self.backend_loop:
            from aeris import process_user_input
            asyncio.run_coroutine_threadsafe(
                process_user_input(self, text, use_tts=False),
                self.backend_loop
            )


    def write_log(self, text):
        if self._mode == "chat":
            self.append_ai_typing(str(text))


    def _modern_icon_button(self, icon, handler):
        return ft.Container(
            content=ft.IconButton(icon=icon, icon_size=20, on_click=handler),
            bgcolor="#1e293b",
            border_radius=14,
            padding=8,
        )


    def _bubble(self, text, user=False):
        align = ft.MainAxisAlignment.END if user else ft.MainAxisAlignment.START
        color = "#2563eb" if user else "#1c2438"

        return ft.Row(
            [
                ft.Container(
                    content=ft.Text(text, selectable=True),
                    bgcolor=color,
                    padding=16,
                    border_radius=16,
                    width=460,
                )
            ],
            alignment=align,
        )


    def _switch(self, mode):
        self._mode = mode
        self._live_view.visible = mode == "live"
        self._chat_view.visible = mode == "chat"
        self._page.update()


    async def _animation_loop(self):

        last = time.perf_counter()

        while self._running:

            now = time.perf_counter()
            dt = min(now - last, 0.03)
            last = now

            self._smoothed_audio += (
                self._audio_level - self._smoothed_audio
            ) * 6 * dt

            state_boost = {
                "idle": 0.0,
                "listening": 0.15,
                "processing": 0.18,
                "speaking": 0.35,
            }.get(self._state, 0.0)

            t = now - self._start_time
            breathe = 0.03 * math.sin(t * 1.8)

            target_scale = 1 + breathe + state_boost + self._smoothed_audio * 0.4
            self._current_scale += (target_scale - self._current_scale) * 8 * dt

            self._core.scale = self._current_scale
            self._glow.scale = self._current_scale * 1.08
            self._glow.opacity = 0.08 + state_boost * 0.7

            self._status.value = self._state.capitalize()

            self._page.update()
            await asyncio.sleep(1 / 60)


    def _set_state_threadsafe(self, state):
        def update():
            self._state = state
        self._safe_ui(update)


    def start_listening(self): self._set_state_threadsafe("listening")
    def stop_listening(self): self._set_state_threadsafe("idle")
    def start_processing(self): self._set_state_threadsafe("processing")
    def stop_processing(self): self._set_state_threadsafe("idle")
    def start_speaking(self): self._set_state_threadsafe("speaking")
    def stop_speaking(self): self._set_state_threadsafe("idle")
    def set_audio_level(self, level): self._audio_level = level


    def run(self):
        ft.app(target=self._main)
