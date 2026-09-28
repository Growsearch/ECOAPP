from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen

from app.services.denuncia_service import DenunciaService

COR_CURTIDO = (0.85, 0.20, 0.35, 1)
COR_NAO_CURTIDO = (0.55, 0.55, 0.55, 1)


class FeedScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = DenunciaService()
        self._ids_curtidas: set = set()

    def on_pre_enter(self):
        self._render()

    def voltar_home(self):
        self.manager.current = "home"

    def _render(self):
        container = self.ids.feed_container
        container.clear_widgets()

        app = MDApp.get_running_app()
        if not app.current_user:
            container.add_widget(MDLabel(text="Faça login para ver o feed."))
            return

        self._ids_curtidas = self.service.ids_curtidas(app.current_user.id)
        denuncias = self.service.listar_feed()

        if not denuncias:
            container.add_widget(
                MDLabel(
                    text="Ainda não há denúncias registradas.",
                    halign="center",
                    theme_text_color="Secondary",
                )
            )
            return

        for d in denuncias:
            container.add_widget(self._card_feed(d))

    def _card_feed(self, d) -> MDCard:
        card = MDCard(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(6),
            size_hint_y=None,
            height=dp(170),
            elevation=2,
            radius=[dp(10)],
            md_bg_color=(1, 1, 1, 1),
        )

        card.add_widget(MDLabel(
            text=f"[b]{d.categoria}[/b]",
            markup=True,
            theme_text_color="Custom",
            text_color=(0.15, 0.45, 0.20, 1),
            size_hint_y=None,
            height=dp(24),
        ))

        bairro_txt = d.bairro or "Bairro não identificado"
        data_fmt = d.criado_em.strftime("%d/%m/%Y %H:%M")
        card.add_widget(MDLabel(
            text=f"{bairro_txt} · CEP {d.cep} · {data_fmt}",
            theme_text_color="Secondary",
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        ))

        card.add_widget(MDLabel(
            text=d.descricao,
            theme_text_color="Primary",
            shorten=True,
            shorten_from="right",
            max_lines=2,
        ))

        acao = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
            spacing=dp(4),
        )
        curtido = d.id in self._ids_curtidas
        icone = "heart" if curtido else "heart-outline"
        cor = COR_CURTIDO if curtido else COR_NAO_CURTIDO

        botao_like = MDIconButton(
            icon=icone,
            theme_icon_color="Custom",
            icon_color=cor,
        )
        contagem = MDLabel(
            text=str(d.likes),
            theme_text_color="Secondary",
            size_hint_x=None,
            width=dp(40),
        )
        botao_like.bind(
            on_release=lambda _btn, denuncia_id=d.id, lbl=contagem, btn=botao_like:
                self._toggle_like(denuncia_id, lbl, btn)
        )
        acao.add_widget(botao_like)
        acao.add_widget(contagem)
        acao.add_widget(MDLabel(text=""))  # spacer
        card.add_widget(acao)

        return card

    def _toggle_like(self, denuncia_id: int, label_contagem: MDLabel, botao: MDIconButton):
        app = MDApp.get_running_app()
        if not app.current_user:
            return
        novo_total = self.service.toggle_curtida(denuncia_id, app.current_user.id)
        label_contagem.text = str(novo_total)
        if denuncia_id in self._ids_curtidas:
            self._ids_curtidas.discard(denuncia_id)
            botao.icon = "heart-outline"
            botao.icon_color = COR_NAO_CURTIDO
        else:
            self._ids_curtidas.add(denuncia_id)
            botao.icon = "heart"
            botao.icon_color = COR_CURTIDO
