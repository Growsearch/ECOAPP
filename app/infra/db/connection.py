import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[3] / "ecoapp.db"

SCHEMA_BASE = """
CREATE TABLE IF NOT EXISTS denuncias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT NOT NULL,
    descricao TEXT NOT NULL,
    cep TEXT NOT NULL,
    cpf_hash TEXT,
    email TEXT NOT NULL,
    telefone TEXT NOT NULL,
    anexo_path TEXT,
    status TEXT NOT NULL,
    criado_em TEXT NOT NULL,
    bairro TEXT,
    usuario_id INTEGER,
    likes INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_denuncias_criado_em ON denuncias(criado_em);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS curtidas (
    usuario_id INTEGER NOT NULL,
    denuncia_id INTEGER NOT NULL,
    criado_em TEXT NOT NULL,
    PRIMARY KEY (usuario_id, denuncia_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (denuncia_id) REFERENCES denuncias(id) ON DELETE CASCADE
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _colunas_existentes(conn: sqlite3.Connection, tabela: str) -> set:
    rows = conn.execute(f"PRAGMA table_info({tabela})").fetchall()
    return {row["name"] for row in rows}


def _coluna_notnull(conn: sqlite3.Connection, tabela: str, coluna: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({tabela})").fetchall()
    for r in rows:
        if r["name"] == coluna:
            return bool(r["notnull"])
    return False


def _tabela_existe(conn: sqlite3.Connection, tabela: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabela,)
    ).fetchone()
    return row is not None


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA_BASE)

        if _tabela_existe(conn, "denuncias"):
            cols = _colunas_existentes(conn, "denuncias")
            if "bairro" not in cols:
                conn.execute("ALTER TABLE denuncias ADD COLUMN bairro TEXT")
            if "usuario_id" not in cols:
                conn.execute("ALTER TABLE denuncias ADD COLUMN usuario_id INTEGER")
            if "likes" not in cols:
                conn.execute(
                    "ALTER TABLE denuncias ADD COLUMN likes INTEGER NOT NULL DEFAULT 0"
                )
            if _coluna_notnull(conn, "denuncias", "cpf_hash"):
                _rebuild_denuncias_cpf_nullable(conn)

        # criados só após a migração para não referenciar colunas inexistentes
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_denuncias_usuario_id ON denuncias(usuario_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_denuncias_bairro ON denuncias(bairro)"
        )


def _rebuild_denuncias_cpf_nullable(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA foreign_keys = OFF;
        CREATE TABLE denuncias_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            descricao TEXT NOT NULL,
            cep TEXT NOT NULL,
            cpf_hash TEXT,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            anexo_path TEXT,
            status TEXT NOT NULL,
            criado_em TEXT NOT NULL,
            bairro TEXT,
            usuario_id INTEGER,
            likes INTEGER NOT NULL DEFAULT 0
        );
        INSERT INTO denuncias_new
            (id, categoria, descricao, cep, cpf_hash, email, telefone,
             anexo_path, status, criado_em, bairro, usuario_id, likes)
        SELECT
            id, categoria, descricao, cep, cpf_hash, email, telefone,
            anexo_path, status, criado_em, bairro, usuario_id, likes
        FROM denuncias;
        DROP TABLE denuncias;
        ALTER TABLE denuncias_new RENAME TO denuncias;
        CREATE INDEX IF NOT EXISTS ix_denuncias_criado_em ON denuncias(criado_em);
        CREATE INDEX IF NOT EXISTS ix_denuncias_usuario_id ON denuncias(usuario_id);
        CREATE INDEX IF NOT EXISTS ix_denuncias_bairro ON denuncias(bairro);
        PRAGMA foreign_keys = ON;
        """
    )
