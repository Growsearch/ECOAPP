from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen


class HomeScreen(MDScreen):
    def on_pre_enter(self):
        app = MDApp.get_running_app()
        if app.current_user:
            self.ids.user_label.text = f"Olá, {app.current_user.email}"

    def ir_para_denuncia(self):
        self.manager.current = "form"

    def ir_para_historico(self):
        self.manager.current = "history"

    def ir_para_grafico(self):
        self.manager.current = "chart"

    def ir_para_feed(self):
        self.manager.current = "feed"

    def sair(self):
        app = MDApp.get_running_app()
        app.current_user = None
        self.manager.current = "login"
