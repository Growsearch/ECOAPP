from pathlib import Path

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

from app.infra.db.connection import init_db
from app.screens.chart_screen import ChartScreen
from app.screens.feed_screen import FeedScreen
from app.screens.form_screen import FormScreen
from app.screens.history_screen import HistoryScreen
from app.screens.home_screen import HomeScreen
from app.screens.login_screen import LoginScreen
from app.screens.success_screen import SuccessScreen

KV_PATH = Path(__file__).resolve().parent / "app" / "screens" / "screens.kv"


class EcoDenunciaApp(MDApp):
    current_user = None

    def build(self):
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.accent_palette = "LightGreen"
        self.theme_cls.theme_style = "Light"

        init_db()
        Builder.load_file(str(KV_PATH))

        sm = MDScreenManager()
        sm.add_widget(LoginScreen())
        sm.add_widget(HomeScreen())
        sm.add_widget(FormScreen())
        sm.add_widget(SuccessScreen())
        sm.add_widget(HistoryScreen())
        sm.add_widget(ChartScreen())
        sm.add_widget(FeedScreen())
        sm.current = "login"
        return sm


if __name__ == "__main__":
    EcoDenunciaApp().run()
