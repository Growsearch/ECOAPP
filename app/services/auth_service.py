import hashlib
import hmac
import os
from typing import Optional

from app.domain.entities import Usuario
from app.domain.validators import ValidationError, validar_email, validar_senha
from app.repositories.usuario_repository import UsuarioRepository

_ITER = 200_000
_SALT_BYTES = 16
_ALG = "sha256"


def _hash_senha(senha: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac(_ALG, senha.encode("utf-8"), salt, _ITER)
    return f"{_ITER}${salt.hex()}${dk.hex()}"


def _verificar(senha: str, senha_hash: str) -> bool:
    try:
        iter_str, salt_hex, dk_hex = senha_hash.split("$")
        iters = int(iter_str)
        salt = bytes.fromhex(salt_hex)
        esperado = bytes.fromhex(dk_hex)
    except (ValueError, AttributeError):
        return False
    calc = hashlib.pbkdf2_hmac(_ALG, senha.encode("utf-8"), salt, iters)
    return hmac.compare_digest(calc, esperado)


class AuthService:
    def __init__(self, repository: Optional[UsuarioRepository] = None):
        self.repository = repository or UsuarioRepository()

    def cadastrar(self, email: str, senha: str) -> Usuario:
        email_ok = validar_email(email)
        validar_senha(senha)
        if self.repository.buscar_por_email(email_ok):
            raise ValidationError("Já existe uma conta com este e-mail.")
        salt = os.urandom(_SALT_BYTES)
        senha_hash = _hash_senha(senha, salt)
        usuario = Usuario(email=email_ok, senha_hash=senha_hash)
        return self.repository.salvar(usuario)

    def autenticar(self, email: str, senha: str) -> Usuario:
        email_ok = validar_email(email)
        usuario = self.repository.buscar_por_email(email_ok)
        if not usuario or not _verificar(senha, usuario.senha_hash):
            raise ValidationError("E-mail ou senha incorretos.")
        return usuario
