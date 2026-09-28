from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from app.domain.entities import CATEGORIAS, Denuncia
from app.domain.validators import (
    ValidationError,
    mascarar_cep,
    validar_cep,
    validar_email,
    validar_telefone,
)
from app.repositories.denuncia_repository import DenunciaRepository


@dataclass
class SerieBairro:
    bairro: str
    valores: List[int]
    total: int


@dataclass
class RelatorioMensal:
    meses: List[str]
    series: List[SerieBairro]


class DenunciaService:
    def __init__(self, repository: Optional[DenunciaRepository] = None):
        self.repository = repository or DenunciaRepository()

    def registrar(
        self,
        *,
        categoria: str,
        descricao: str,
        cep: str,
        email: str,
        telefone: str,
        usuario_id: int,
        anexo_path: Optional[str] = None,
        bairro: Optional[str] = None,
    ) -> Denuncia:
        if categoria not in CATEGORIAS:
            raise ValidationError("Categoria inválida.")
        if not (descricao or "").strip():
            raise ValidationError("Descrição não pode ser vazia.")

        email_ok = validar_email(email)
        telefone_ok = validar_telefone(telefone)
        cep_ok = validar_cep(cep)

        denuncia = Denuncia(
            categoria=categoria,
            descricao=descricao.strip(),
            cep=mascarar_cep(cep_ok),
            email=email_ok,
            telefone=telefone_ok,
            anexo_path=anexo_path,
            bairro=(bairro or "").strip() or None,
            usuario_id=usuario_id,
        )
        return self.repository.salvar(denuncia)

    def listar_minhas(self, usuario_id: int) -> List[Denuncia]:
        return self.repository.listar(usuario_id=usuario_id)

    def listar_feed(self) -> List[Denuncia]:
        return self.repository.listar(usuario_id=None)

    def deletar(self, denuncia_id: int, usuario_id: int) -> bool:
        return self.repository.deletar(denuncia_id, usuario_id)

    def toggle_curtida(self, denuncia_id: int, usuario_id: int) -> int:
        return self.repository.toggle_curtida(denuncia_id, usuario_id)

    def ids_curtidas(self, usuario_id: int) -> set:
        return self.repository.ids_curtidas_por(usuario_id)

    def relatorio_por_bairro(
        self, meses: int = 6, top_n: int = 5
    ) -> RelatorioMensal:
        if meses < 1:
            meses = 1
        if top_n < 1:
            top_n = 1

        hoje = datetime.now()
        desde = _inicio_janela_mensal(hoje, meses)
        agregados = self.repository.agregar_por_bairro_mes(desde=desde)

        meses_labels = _labels_meses(hoje, meses)
        indice_mes = {label: i for i, label in enumerate(meses_labels)}

        totais_por_bairro: dict[str, int] = {}
        matriz: dict[str, List[int]] = {}
        for a in agregados:
            if a.ym not in indice_mes:
                continue
            valores = matriz.setdefault(a.bairro, [0] * meses)
            valores[indice_mes[a.ym]] += a.total
            totais_por_bairro[a.bairro] = totais_por_bairro.get(a.bairro, 0) + a.total

        top_bairros = sorted(
            totais_por_bairro.items(), key=lambda kv: kv[1], reverse=True
        )[:top_n]

        series = [
            SerieBairro(bairro=nome, valores=matriz[nome], total=total)
            for nome, total in top_bairros
        ]
        return RelatorioMensal(meses=meses_labels, series=series)


def _inicio_janela_mensal(referencia: datetime, meses: int) -> datetime:
    ano = referencia.year
    mes = referencia.month - (meses - 1)
    while mes <= 0:
        mes += 12
        ano -= 1
    return datetime(ano, mes, 1)


def _labels_meses(referencia: datetime, meses: int) -> List[str]:
    labels: List[str] = []
    ano = referencia.year
    mes = referencia.month - (meses - 1)
    while mes <= 0:
        mes += 12
        ano -= 1
    for _ in range(meses):
        labels.append(f"{ano:04d}-{mes:02d}")
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return labels
