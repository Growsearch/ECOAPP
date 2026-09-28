from datetime import datetime
from typing import Optional

from app.domain.entities import Usuario
from app.infra.db.connection import get_connection


class UsuarioRepository:
    def salvar(self, usuario: Usuario) -> Usuario:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO usuarios (email, senha_hash, criado_em)
                VALUES (?, ?, ?)
                """,
                (usuario.email, usuario.senha_hash, usuario.criado_em.isoformat()),
            )
            usuario.id = cur.lastrowid
            return usuario

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM usuarios WHERE email = ?", (email,)
            ).fetchone()
        if not row:
            return None
        return Usuario(
            id=row["id"],
            email=row["email"],
            senha_hash=row["senha_hash"],
            criado_em=datetime.fromisoformat(row["criado_em"]),
        )
