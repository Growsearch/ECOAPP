import re


class ValidationError(ValueError):
    pass


def only_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def validar_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValidationError("E-mail inválido.")
    return email


def validar_senha(senha: str) -> str:
    if not senha or len(senha) < 6:
        raise ValidationError("A senha deve ter pelo menos 6 caracteres.")
    return senha


def validar_telefone(telefone: str) -> str:
    digits = only_digits(telefone)
    if len(digits) < 10 or len(digits) > 11:
        raise ValidationError("Telefone inválido (use DDD + número).")
    return digits


def validar_cep(cep: str) -> str:
    digits = only_digits(cep)
    if len(digits) != 8:
        raise ValidationError("CEP inválido (8 dígitos).")
    return digits


def mascarar_cep(cep_digits: str) -> str:
    return f"{cep_digits[:5]}-{cep_digits[5:]}"
