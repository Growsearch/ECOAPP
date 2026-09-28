import json
import os

from kivy.network.urlrequest import UrlRequest
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen

from app.domain.entities import CATEGORIAS
from app.domain.validators import ValidationError, only_digits
from app.services.denuncia_service import DenunciaService

CATEGORIA_PLACEHOLDER = "Selecionar categoria"
EXTENSOES_IMAGEM = [".png", ".jpg", ".jpeg", ".webp"]


class FormScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = DenunciaService()
        self._menu = None
        self._dialog = None
        self._file_manager = None
        self._anexo_path = None
        self._bairro = None

    def on_pre_enter(self):
        self._reset_form()

    def abrir_categorias(self, caller):
        items = [
            {
                "text": cat,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=cat: self._selecionar_categoria(x),
            }
            for cat in CATEGORIAS
        ]
        self._menu = MDDropdownMenu(caller=caller, items=items, width_mult=4)
        self._menu.open()

    def _selecionar_categoria(self, categoria: str):
        self.ids.categoria_btn.text = categoria
        if self._menu:
            self._menu.dismiss()

    def selecionar_anexo(self):
        if self._file_manager is None:
            self._file_manager = MDFileManager(
                exit_manager=self._fechar_file_manager,
                select_path=self._anexo_selecionado,
                ext=EXTENSOES_IMAGEM,
                preview=True,
            )
        self._file_manager.show(os.path.expanduser("~"))

    def _fechar_file_manager(self, *_):
        if self._file_manager:
            self._file_manager.close()

    def _anexo_selecionado(self, path: str):
        self._anexo_path = path
        self.ids.anexo_label.text = f"Anexo: {os.path.basename(path)}"
        self._fechar_file_manager()

    def cep_alterado(self, novo_valor: str):
        self._bairro = None

    def buscar_cep(self):
        cep_digits = only_digits(self.ids.cep_field.text)
        if len(cep_digits) != 8:
            self._alerta("CEP deve ter 8 dígitos.")
            return
        self._bairro = None
        self.ids.cep_status.text = "Buscando CEP..."
        UrlRequest(
            f"https://viacep.com.br/ws/{cep_digits}/json/",
            on_success=self._on_cep_ok,
            on_failure=self._on_cep_falha,
            on_error=self._on_cep_erro,
            timeout=8,
        )

    def _on_cep_ok(self, _req, result):
        parsed = result
        if isinstance(parsed, (bytes, str)):
            try:
                parsed = json.loads(parsed)
            except Exception:
                self.ids.cep_status.text = "Resposta inválida do serviço de CEP."
                return
        if not isinstance(parsed, dict) or parsed.get("erro"):
            self.ids.cep_status.text = "CEP não encontrado."
            return
        logradouro = parsed.get("logradouro", "")
        bairro = parsed.get("bairro", "")
        localidade = parsed.get("localidade", "")
        uf = parsed.get("uf", "")
        self._bairro = (bairro or "").strip() or None
        loc = f"{localidade}/{uf}" if localidade and uf else localidade
        partes = [p for p in (logradouro, bairro, loc) if p]
        self.ids.cep_status.text = " · ".join(partes) or "CEP válido."

    def _on_cep_falha(self, _req, _result):
        self.ids.cep_status.text = "CEP não encontrado."

    def _on_cep_erro(self, _req, _err):
        self.ids.cep_status.text = "Falha ao consultar CEP (verifique a internet)."

    def enviar(self):
        app = MDApp.get_running_app()
        if not app.current_user:
            self._alerta("Sessão expirada. Faça login novamente.")
            self.manager.current = "login"
            return

        obrigatorios = {
            "E-mail de contato": self.ids.email_field.text,
            "Telefone": self.ids.telefone_field.text,
            "CEP": self.ids.cep_field.text,
            "Descrição": self.ids.descricao_field.text,
        }
        vazios = [nome for nome, val in obrigatorios.items() if not (val or "").strip()]
        categoria = self.ids.categoria_btn.text
        if categoria == CATEGORIA_PLACEHOLDER:
            vazios.insert(0, "Categoria")

        if vazios:
            self._alerta("Preencha os campos obrigatórios:\n• " + "\n• ".join(vazios))
            return

        try:
            denuncia = self.service.registrar(
                categoria=categoria,
                descricao=self.ids.descricao_field.text,
                cep=self.ids.cep_field.text,
                email=self.ids.email_field.text,
                telefone=self.ids.telefone_field.text,
                anexo_path=self._anexo_path,
                bairro=self._bairro,
                usuario_id=app.current_user.id,
            )
        except ValidationError as e:
            self._alerta(str(e))
            return

        sucesso = self.manager.get_screen("success")
        sucesso.set_categoria(denuncia.categoria)
        self.manager.current = "success"

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

    def _reset_form(self):
        for field in (
            "descricao_field",
            "cep_field",
            "email_field",
            "telefone_field",
        ):
            self.ids[field].text = ""
        app = MDApp.get_running_app()
        if app.current_user:
            self.ids.email_field.text = app.current_user.email
        self.ids.categoria_btn.text = CATEGORIA_PLACEHOLDER
        self.ids.anexo_label.text = "Nenhum anexo selecionado"
        self.ids.cep_status.text = ""
        self._anexo_path = None
        self._bairro = None
