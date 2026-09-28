from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen

from app.domain.validators import ValidationError
from app.services.auth_service import AuthService


class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth = AuthService()
        self._dialog = None
        self._modo_cadastro = False

    def on_pre_enter(self):
        self.ids.email_field.text = ""
        self.ids.senha_field.text = ""
        self._aplicar_modo()

    def alternar_modo(self):
        self._modo_cadastro = not self._modo_cadastro
        self._aplicar_modo()

    def _aplicar_modo(self):
        if self._modo_cadastro:
            self.ids.titulo.text = "Criar Conta"
            self.ids.acao_btn.text = "Cadastrar"
            self.ids.alternar_btn.text = "Já tenho conta"
        else:
            self.ids.titulo.text = "Entrar"
            self.ids.acao_btn.text = "Entrar"
            self.ids.alternar_btn.text = "Criar nova conta"

    def submeter(self):
        email = self.ids.email_field.text
        senha = self.ids.senha_field.text
        try:
            if self._modo_cadastro:
                usuario = self.auth.cadastrar(email, senha)
            else:
                usuario = self.auth.autenticar(email, senha)
        except ValidationError as e:
            self._alerta(str(e))
            return
        except Exception as e:  # noqa: BLE001
            self._alerta(f"Erro inesperado: {e}")
            return

        app = MDApp.get_running_app()
        app.current_user = usuario
        self.manager.current = "home"

    def _alerta(self, msg: str):
        if self._dialog:
            self._dialog.dismiss()
        self._dialog = MDDialog(
            title="Atenção",
            text=msg,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda *_: self._dialog.dismiss(),
                )
            ],
        )
        self._dialog.open()
