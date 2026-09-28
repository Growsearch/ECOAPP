from typing import List, Tuple

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen

from app.services.denuncia_service import DenunciaService, RelatorioMensal

PALETA: List[Tuple[float, float, float, float]] = [
    (0.15, 0.55, 0.25, 1),
    (0.85, 0.45, 0.10, 1),
    (0.20, 0.40, 0.75, 1),
    (0.70, 0.20, 0.55, 1),
    (0.90, 0.75, 0.10, 1),
]

JANELA_MESES = 6
TOP_BAIRROS = 5
LINE_WIDTH_DP = 2.5

MESES_PT = {
    "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
    "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
    "09": "Set", "10": "Out", "11": "Nov", "12": "Dez",
}


class ChartScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = DenunciaService()

    def on_pre_enter(self):
        self._mostrar_estado("Carregando dados...")
        Clock.schedule_once(lambda _dt: self._carregar(), 0)

    def voltar_home(self):
        self.manager.current = "home"

    def _carregar(self):
        try:
            relatorio = self.service.relatorio_por_bairro(
                meses=JANELA_MESES, top_n=TOP_BAIRROS
            )
        except Exception as e:  # noqa: BLE001
            self._mostrar_estado(f"Erro ao carregar dados:\n{e}")
            return

        if not relatorio.series or all(s.total == 0 for s in relatorio.series):
            self._mostrar_estado(
                "Ainda não há denúncias registradas nos últimos meses.\n"
                "Registre denúncias e o gráfico aparecerá aqui."
            )
            return

        try:
            self._renderizar(relatorio)
        except ImportError:
            self._mostrar_estado(
                "Biblioteca de gráficos ausente.\n"
                "Instale com: pip install kivy_garden.graph"
            )
        except Exception as e:  # noqa: BLE001
            self._mostrar_estado(f"Erro ao renderizar gráfico:\n{e}")

    def _mostrar_estado(self, mensagem: str):
        self.ids.chart_container.clear_widgets()
        self.ids.legenda_container.clear_widgets()
        self.ids.stats_container.clear_widgets()
        self.ids.meses_label.text = ""
        self.ids.chart_container.add_widget(
            MDLabel(
                text=mensagem,
                halign="center",
                theme_text_color="Secondary",
            )
        )

    def _renderizar(self, relatorio: RelatorioMensal):
        from kivy_garden.graph import Graph, LinePlot

        container = self.ids.chart_container
        legenda = self.ids.legenda_container
        stats = self.ids.stats_container
        container.clear_widgets()
        legenda.clear_widgets()
        stats.clear_widgets()

        total_periodo = sum(s.total for s in relatorio.series)
        bairro_top = relatorio.series[0]
        pico_mes, pico_valor = _mes_pico(relatorio)
        periodo_txt = f"{_mes_curto(relatorio.meses[0])} → {_mes_curto(relatorio.meses[-1])}"

        stats.add_widget(_StatTile("Total", str(total_periodo), "denúncias no período"))
        stats.add_widget(_StatTile("Top bairro", bairro_top.bairro, f"{bairro_top.total} caso(s)"))
        stats.add_widget(_StatTile("Pico", _mes_curto(pico_mes), f"{pico_valor} no mês"))
        stats.add_widget(_StatTile("Período", periodo_txt, f"{len(relatorio.meses)} meses"))

        y_max = max((max(s.valores) for s in relatorio.series), default=1)
        y_max = max(y_max, 1)
        n_meses = len(relatorio.meses)

        graph = Graph(
            xlabel="",
            ylabel="Denúncias",
            x_ticks_major=1,
            y_ticks_major=max(1, y_max // 4),
            y_grid_label=True,
            x_grid_label=True,
            padding=dp(4),
            x_grid=True,
            y_grid=True,
            xmin=1,
            xmax=n_meses,
            ymin=0,
            ymax=y_max + 1,
            border_color=[0.7, 0.75, 0.7, 1],
            tick_color=[0.6, 0.65, 0.6, 1],
            label_options={"color": (0.2, 0.25, 0.2, 1), "bold": False},
        )

        for i, serie in enumerate(relatorio.series):
            cor = PALETA[i % len(PALETA)]
            plot = LinePlot(color=list(cor), line_width=LINE_WIDTH_DP)
            plot.points = [(x + 1, v) for x, v in enumerate(serie.valores)]
            graph.add_plot(plot)
            legenda.add_widget(
                _LegendaItem(cor=cor, texto=serie.bairro, total=serie.total)
            )

        container.add_widget(graph)

        rodape = "Meses:  " + "   ".join(
            f"[b]{i + 1}[/b] {_mes_curto(label)}"
            for i, label in enumerate(relatorio.meses)
        )
        self.ids.meses_label.text = rodape


def _mes_pico(relatorio: RelatorioMensal) -> Tuple[str, int]:
    totais_por_mes = [0] * len(relatorio.meses)
    for s in relatorio.series:
        for i, v in enumerate(s.valores):
            totais_por_mes[i] += v
    idx = max(range(len(totais_por_mes)), key=lambda i: totais_por_mes[i])
    return relatorio.meses[idx], totais_por_mes[idx]


def _mes_curto(ym: str) -> str:
    ano, mes = ym.split("-")
    return f"{MESES_PT.get(mes, mes)}/{ano[-2:]}"


class _StatTile(MDCard):
    def __init__(self, rotulo: str, valor: str, sublabel: str, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=dp(10),
            size_hint_x=1,
            size_hint_y=None,
            height=dp(88),
            md_bg_color=(1, 1, 1, 1),
            radius=[dp(10)],
            elevation=1,
            **kwargs,
        )
        self.add_widget(MDLabel(
            text=rotulo,
            font_style="Overline",
            theme_text_color="Secondary",
            adaptive_height=True,
        ))
        self.add_widget(MDLabel(
            text=valor,
            font_style="H6",
            theme_text_color="Custom",
            text_color=(0.15, 0.45, 0.20, 1),
            bold=True,
            adaptive_height=True,
            shorten=True,
            shorten_from="right",
        ))
        self.add_widget(MDLabel(
            text=sublabel,
            font_style="Caption",
            theme_text_color="Secondary",
            adaptive_height=True,
        ))


class _LegendaItem(MDBoxLayout):
    def __init__(self, cor, texto: str, total: int, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(24),
            spacing=dp(8),
            **kwargs,
        )
        r, g, b, _ = cor
        marcador_hex = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        self.add_widget(MDLabel(
            text=f"[color={marcador_hex}]■[/color]",
            markup=True,
            size_hint_x=None,
            width=dp(18),
            halign="left",
        ))
        self.add_widget(MDLabel(
            text=texto,
            theme_text_color="Primary",
            shorten=True,
            shorten_from="right",
        ))
        self.add_widget(MDLabel(
            text=str(total),
            theme_text_color="Custom",
            text_color=(0.15, 0.45, 0.20, 1),
            bold=True,
            size_hint_x=None,
            width=dp(40),
            halign="right",
        ))
