from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen

from app.services.denuncia_service import DenunciaService


class HistoryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = DenunciaService()
        self._dialog = None

    def on_pre_enter(self):
        self._render_lista()

    def voltar_home(self):
        self.manager.current = "home"

    def _render_lista(self):
        container = self.ids.lista_container
        container.clear_widgets()

        app = MDApp.get_running_app()
        if not app.current_user:
            container.add_widget(MDLabel(text="Faça login para ver suas denúncias."))
            return

        denuncias = self.service.listar_minhas(app.current_user.id)
        if not denuncias:
            container.add_widget(
                MDLabel(
                    text="Você ainda não registrou denúncias.",
                    halign="center",
                    theme_text_color="Secondary",
                )
            )
            return

        for d in denuncias:
            container.add_widget(self._card_denuncia(d))

    def _card_denuncia(self, d) -> MDCard:
        card = MDCard(
            orientation="horizontal",
            padding=dp(12),
            size_hint_y=None,
            height=dp(120),
            elevation=2,
            radius=[dp(10)],
            md_bg_color=(1, 1, 1, 1),
        )

        info = MDBoxLayout(orientation="vertical", spacing=dp(2))
        info.add_widget(MDLabel(
            text=f"[b]{d.categoria}[/b]",
            markup=True,
            theme_text_color="Custom",
            text_color=(0.15, 0.45, 0.20, 1),
        ))
        data_fmt = d.criado_em.strftime("%d/%m/%Y %H:%M")
        bairro_txt = d.bairro or "Bairro não identificado"
        info.add_widget(MDLabel(
            text=f"{bairro_txt} · CEP {d.cep}",
            theme_text_color="Secondary",
            font_style="Caption",
        ))
        info.add_widget(MDLabel(
            text=data_fmt,
            theme_text_color="Secondary",
            font_style="Caption",
        ))
        info.add_widget(MDLabel(
            text=f"Status: {d.status}   ♥ {d.likes}",
            theme_text_color="Custom",
            text_color=(0.15, 0.55, 0.25, 1),
            font_style="Caption",
        ))
        card.add_widget(info)

        botao = MDIconButton(
            icon="delete-outline",
            theme_icon_color="Custom",
            icon_color=(0.75, 0.20, 0.20, 1),
            pos_hint={"center_y": 0.5},
        )
        botao.bind(on_release=lambda _btn, denuncia_id=d.id: self._confirmar_exclusao(denuncia_id))
        card.add_widget(botao)

        return card

    def _confirmar_exclusao(self, denuncia_id: int):
        if self._dialog:
            self._dialog.dismiss()
        self._dialog = MDDialog(
            title="Excluir denúncia?",
            text="Esta ação não pode ser desfeita.",
            buttons=[
                MDFlatButton(
                    text="Cancelar",
                    on_release=lambda *_: self._dialog.dismiss(),
                ),
                MDFlatButton(
                    text="Excluir",
                    theme_text_color="Custom",
                    text_color=(0.75, 0.20, 0.20, 1),
                    on_release=lambda *_: self._excluir(denuncia_id),
                ),
            ],
        )
        self._dialog.open()

    def _excluir(self, denuncia_id: int):
        if self._dialog:
            self._dialog.dismiss()
        app = MDApp.get_running_app()
        if not app.current_user:
            return
        self.service.deletar(denuncia_id, app.current_user.id)
        self._render_lista()
