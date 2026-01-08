import flet as ft
import asyncio
import datetime
import sqlite3
import random
import os

# --- Safe Import for Quotes ---
try:
    from quotes import quotes
except ImportError:
    quotes = [
        "Focus on being productive instead of busy.",
        "The secret of getting ahead is getting started.",
        "It always seems impossible until it is done.",
        "Don't watch the clock; do what it does. Keep going.",
        "Discipline is doing what needs to be done, even if you don't want to do it."
    ]

# --- 1. System Configuration ---
DEFAULT_TARGET_HOURS = 10
CHECK_IN_INTERVAL = 15 * 60


class DisciplineApp:
    def __init__(self):
        # Android Fix: Ensure DB is created in a writeable location implies default handling
        # Flet on Android typically handles relative paths in the user data dir safely.
        self.db_name = "discipline.db"
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.create_tables()
        self.is_working = False
        self.start_time = None
        self.worked_seconds = 0
        self.daily_target = DEFAULT_TARGET_HOURS
        self.current_task_focus = "General Work"

        # --- 2. Database Layer ---

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hourly_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                activity TEXT,
                productivity_score INTEGER
            )
        ''')
        self.conn.commit()

    def log_activity(self, activity_text, score=0):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO hourly_logs (timestamp, activity, productivity_score) VALUES (?, ?, ?)",
                       (datetime.datetime.now(), activity_text, score))
        self.conn.commit()


# --- 3. UI Layer ---
def main(page: ft.Page):
    page.title = "Hardcore Discipline"
    page.rtl = True
    page.theme_mode = ft.ThemeMode.DARK

    # Mobile Optimization: Adaptive Alignment & Scroll
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.scroll = ft.ScrollMode.ADAPTIVE

    # Mobile Optimization: Enable SafeArea to avoid camera notch issues
    page.safe_area = True

    app_logic = DisciplineApp()

    # --- UI Elements ---

    # 1. Goal Selector
    target_dropdown = ft.Dropdown(
        label="هدف الساعات اليومي",
        value=str(DEFAULT_TARGET_HOURS),
        options=[
            ft.dropdown.Option("3"),
            ft.dropdown.Option("5"),
            ft.dropdown.Option("8"),
            ft.dropdown.Option("10"),
            ft.dropdown.Option("12"),
        ],
        # Mobile UX: Make it fill width for easier tapping
        expand=True
    )

    def on_target_change(e):
        app_logic.daily_target = int(target_dropdown.value)
        page.update()

    target_dropdown.on_change = on_target_change

    # 2. Timer & Focus Display
    timer_text = ft.Text("00:00:00", size=50, weight=ft.FontWeight.BOLD)  # Bigger for phone

    current_focus_label = ft.Text(
        value=f"🎯 التركيز الحالي: {app_logic.current_task_focus}",
        size=16,
        color=ft.Colors.CYAN_ACCENT,
        weight=ft.FontWeight.BOLD
    )

    status_text = ft.Text("هل أنت مستعد للبدء؟", size=14, color=ft.Colors.GREY)

    progress_bar = ft.ProgressBar(value=0, color=ft.Colors.GREEN)  # Removed fixed width

    # 3. Task Management Elements
    task_input = ft.TextField(
        hint_text="أضف مهمة...",
        expand=True,
        height=50,
        content_padding=15
    )

    tasks_column = ft.Column()

    def set_focus_task(task_name):
        app_logic.current_task_focus = task_name
        current_focus_label.value = f"🎯 التركيز الحالي: {task_name}"
        page.update()

    def delete_task(task_row, task_control):
        tasks_column.controls.remove(task_control)
        page.update()

    def add_task(e):
        if not task_input.value:
            return

        task_text = task_input.value
        task_row_control = ft.Container()

        def on_delete_click(e):
            delete_task(task_text, task_row_control)

        def on_focus_click(e):
            set_focus_task(task_text)

        row_content = ft.Row(
            controls=[
                ft.Checkbox(value=False),
                ft.Text(task_text, expand=True, size=18, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.IconButton(icon=ft.Icons.TRACK_CHANGES, icon_color=ft.Colors.BLUE_400, on_click=on_focus_click),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, on_click=on_delete_click)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        task_row_control.content = row_content
        task_row_control.padding = ft.Padding(0, 5, 0, 5)

        tasks_column.controls.append(task_row_control)
        task_input.value = ""
        page.update()

    add_task_btn = ft.IconButton(
        icon=ft.Icons.ADD_CIRCLE,
        icon_color=ft.Colors.GREEN_400,
        icon_size=30,
        on_click=add_task
    )

    # 4. Quotes & Logs
    quote_text = ft.Text(
        value="توكل على الله",
        size=16,
        color=ft.Colors.CYAN_200,
        text_align=ft.TextAlign.CENTER,
        italic=True
    )

    note_input = ft.TextField(label="ملاحظة (اختياري)", multiline=True)

    # --- Button Internal Controls ---
    btn_label_control = ft.Text("بدء يوم العمل", color=ft.Colors.WHITE, size=18)
    btn_icon_control = ft.Icon(ft.Icons.PLAY_ARROW, color=ft.Colors.WHITE)

    # --- Logic Functions ---

    def update_quote():
        if quotes:
            random_quote = random.choice(quotes)
            quote_text.value = f'"{random_quote}"'
            page.update()

    def handle_yes(e):
        note = f" - ملاحظة: {note_input.value}" if note_input.value else ""
        app_logic.log_activity(f"إجابة: نعم{note}", score=1)
        note_input.value = ""
        page.close_dialog()
        page.snack_bar = ft.SnackBar(ft.Text("أحسنت! استمر 🔥", color=ft.Colors.WHITE))
        page.snack_bar.open = True
        page.update()

    def handle_no(e):
        note = f" - ملاحظة: {note_input.value}" if note_input.value else ""
        app_logic.log_activity(f"إجابة: لا{note}", score=0)
        note_input.value = ""
        page.close_dialog()
        page.snack_bar = ft.SnackBar(ft.Text("عد للتركيز فوراً ⚠️", color=ft.Colors.RED_200))
        page.snack_bar.open = True
        page.update()

    log_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("🛑 تفتيش الوعي"),
        content=ft.Column(
            [
                ft.Text("هل تستثمر في وقتك حالياً؟", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                note_input,
            ],
            height=150,
            tight=True
        ),
        actions=[
            ft.TextButton("نعم", on_click=handle_yes, style=ft.ButtonStyle(color=ft.Colors.GREEN)),
            ft.TextButton("لا", on_click=handle_no, style=ft.ButtonStyle(color=ft.Colors.RED)),
        ],
        actions_alignment=ft.MainAxisAlignment.START,
    )

    # --- Background Timer Logic ---
    async def run_timer():
        while app_logic.is_working:
            app_logic.worked_seconds += 1
            mins, secs = divmod(app_logic.worked_seconds, 60)
            hours, mins = divmod(mins, 60)
            timer_text.value = "{:02d}:{:02d}:{:02d}".format(hours, mins, secs)

            progress = app_logic.worked_seconds / (app_logic.daily_target * 3600)
            progress_bar.value = min(progress, 1.0)

            if app_logic.worked_seconds % CHECK_IN_INTERVAL == 0 and app_logic.worked_seconds > 0:
                page.dialog = log_dialog
                page.dialog.open = True

                # Vibrate on phone (Android only feature support varies, standard SnackBar fallback)
                page.snack_bar = ft.SnackBar(ft.Text("🔔 سؤال الوعي!"))
                page.snack_bar.open = True

            page.update()
            await asyncio.sleep(1)

    async def start_work(e):
        if not app_logic.is_working:
            app_logic.is_working = True
            app_logic.start_time = datetime.datetime.now()

            update_quote()

            btn_label_control.value = "توقف (استراحة)"
            start_btn.style = ft.ButtonStyle(bgcolor=ft.Colors.RED_900)
            status_text.value = "🔥 وضع العمل مفعل"
            target_dropdown.disabled = True
            page.update()
            await run_timer()
        else:
            app_logic.is_working = False
            btn_label_control.value = "بدء يوم العمل"
            start_btn.style = ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700)
            status_text.value = "تم الإيقاف المؤقت"
            target_dropdown.disabled = False
            page.update()

    start_btn = ft.FilledButton(
        content=ft.Row(
            [
                btn_icon_control,
                btn_label_control
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        ),
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700),
        on_click=start_work,
        height=60,  # Taller button for easier touch
        width=250
    )

    update_quote()

    border_side_config = ft.BorderSide(1, ft.Colors.GREY_800)

    # --- Mobile Layout Assembly ---
    # Using ListView to ensure scrolling works perfectly on small screens
    page.add(
        ft.Column(
            [
                ft.Container(height=10),

                # Header Section
                ft.Container(
                    content=ft.Column([
                        ft.Text("⚙️ الهدف اليومي", size=14, color=ft.Colors.GREY_400),
                        target_dropdown,
                    ]),
                    padding=10
                ),

                ft.Divider(height=10, color=ft.Colors.GREY_800),

                # Timer Section (Center Stage)
                ft.Container(
                    content=ft.Column([
                        timer_text,
                        current_focus_label,
                        ft.Container(height=10),
                        progress_bar,
                        ft.Container(height=20),
                        start_btn,
                        ft.Container(height=10),
                        status_text,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=20
                ),

                ft.Divider(height=20, color=ft.Colors.GREY_800),

                # Tasks Section
                ft.Container(
                    content=ft.Column([
                        ft.Text("📝 المهام (Checklist)", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row([task_input, add_task_btn]),
                        ft.Container(height=10),
                        ft.Container(
                            content=tasks_column,
                            padding=10,
                            border=ft.Border(
                                top=border_side_config, bottom=border_side_config,
                                left=border_side_config, right=border_side_config
                            ),
                            border_radius=10,
                        )
                    ]),
                    padding=10
                ),

                ft.Container(height=20),
                quote_text,
                ft.Container(height=30),  # Bottom padding for scrolling
            ],
            scroll=ft.ScrollMode.ADAPTIVE
        )
    )


ft.app(target=main)