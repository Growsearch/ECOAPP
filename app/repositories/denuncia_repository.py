from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from app.domain.entities import Denuncia
from app.infra.db.connection import get_connection


@dataclass
class AgregacaoBairroMes:
    ym: str
    bairro: str
    total: int


class DenunciaRepository:
    def salvar(self, denuncia: Denuncia) -> Denuncia:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO denuncias
                    (categoria, descricao, cep, cpf_hash, email, telefone,
                     anexo_path, bairro, status, criado_em, usuario_id, likes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    denuncia.categoria,
                    denuncia.descricao,
                    denuncia.cep,
                    None,
                    denuncia.email,
                    denuncia.telefone,
                    denuncia.anexo_path,
                    denuncia.bairro,
                    denuncia.status,
                    denuncia.criado_em.isoformat(),
                    denuncia.usuario_id,
                    denuncia.likes,
                ),
            )
            denuncia.id = cur.lastrowid
            return denuncia

    def listar(self, usuario_id: Optional[int] = None) -> List[Denuncia]:
        with get_connection() as conn:
            if usuario_id is None:
                rows = conn.execute(
                    "SELECT * FROM denuncias ORDER BY criado_em DESC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM denuncias WHERE usuario_id = ? ORDER BY criado_em DESC",
                    (usuario_id,),
                ).fetchall()
        return [self._row_to_entity(row) for row in rows]

    def deletar(self, denuncia_id: int, usuario_id: int) -> bool:
        with get_connection() as conn:
            cur = conn.execute(
                "DELETE FROM denuncias WHERE id = ? AND usuario_id = ?",
                (denuncia_id, usuario_id),
            )
            return cur.rowcount > 0

    def toggle_curtida(self, denuncia_id: int, usuario_id: int) -> int:
        """Alterna curtida e retorna o novo total de likes da denúncia."""
        with get_connection() as conn:
            existente = conn.execute(
                "SELECT 1 FROM curtidas WHERE usuario_id = ? AND denuncia_id = ?",
                (usuario_id, denuncia_id),
            ).fetchone()
            if existente:
                conn.execute(
                    "DELETE FROM curtidas WHERE usuario_id = ? AND denuncia_id = ?",
                    (usuario_id, denuncia_id),
                )
                conn.execute(
                    "UPDATE denuncias SET likes = MAX(likes - 1, 0) WHERE id = ?",
                    (denuncia_id,),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO curtidas (usuario_id, denuncia_id, criado_em)
                    VALUES (?, ?, ?)
                    """,
                    (usuario_id, denuncia_id, datetime.now().isoformat()),
                )
                conn.execute(
                    "UPDATE denuncias SET likes = likes + 1 WHERE id = ?",
                    (denuncia_id,),
                )
            row = conn.execute(
                "SELECT likes FROM denuncias WHERE id = ?", (denuncia_id,)
            ).fetchone()
            return row["likes"] if row else 0

    def ids_curtidas_por(self, usuario_id: int) -> set:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT denuncia_id FROM curtidas WHERE usuario_id = ?",
                (usuario_id,),
            ).fetchall()
        return {row["denuncia_id"] for row in rows}

    def agregar_por_bairro_mes(
        self, desde: datetime
    ) -> List[AgregacaoBairroMes]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    strftime('%Y-%m', criado_em) AS ym,
                    COALESCE(NULLIF(TRIM(bairro), ''), 'Não identificado') AS bairro,
                    COUNT(*) AS total
                FROM denuncias
                WHERE criado_em >= ?
                GROUP BY ym, bairro
                ORDER BY ym ASC
                """,
                (desde.isoformat(),),
            ).fetchall()
        return [
            AgregacaoBairroMes(ym=row["ym"], bairro=row["bairro"], total=row["total"])
            for row in rows
        ]

    def _row_to_entity(self, row) -> Denuncia:
        return Denuncia(
            id=row["id"],
            categoria=row["categoria"],
            descricao=row["descricao"],
            cep=row["cep"],
            email=row["email"],
            telefone=row["telefone"],
            anexo_path=row["anexo_path"],
            bairro=row["bairro"],
            status=row["status"],
            criado_em=datetime.fromisoformat(row["criado_em"]),
            usuario_id=row["usuario_id"],
            likes=row["likes"] if row["likes"] is not None else 0,
        )
