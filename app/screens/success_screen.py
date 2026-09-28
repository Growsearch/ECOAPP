from kivymd.uix.screen import MDScreen

from app.services.base_legal_service import BaseLegalService


class SuccessScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_legal = BaseLegalService()
        self._categoria = ""

    def set_categoria(self, categoria: str):
        self._categoria = categoria

    def on_pre_enter(self):
        amparo = self.base_legal.obter_amparo(self._categoria)
        self.ids.artigo_label.text = amparo["artigo"]
        self.ids.texto_label.text = amparo["texto"]
        canais = "\n".join(f"• {c}" for c in amparo["canais"])
        self.ids.canais_label.text = canais

    def voltar_home(self):
        self.manager.current = "home"
