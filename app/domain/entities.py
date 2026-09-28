from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


CATEGORIAS = [
    "Lixo Irregular",
    "Queimada",
    "Desmatamento/Poda Ilegal",
    "Poluição de Água",
    "Maus-Tratos a Animais",
]

STATUS_ENVIADO = "Enviado"


@dataclass
class Usuario:
    email: str
    senha_hash: str
    criado_em: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None


@dataclass
class Denuncia:
    categoria: str
    descricao: str
    cep: str
    email: str
    telefone: str
    anexo_path: Optional[str] = None
    bairro: Optional[str] = None
    status: str = STATUS_ENVIADO
    criado_em: datetime = field(default_factory=datetime.now)
    usuario_id: Optional[int] = None
    likes: int = 0
    id: Optional[int] = None
