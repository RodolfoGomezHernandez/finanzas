from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def miles(valor):
    if valor is None or valor == "":
        return ""
    try:
        numero = Decimal(valor).quantize(Decimal("1"))
    except (InvalidOperation, TypeError, ValueError):
        return valor

    texto = f"{int(numero):,}"
    return texto.replace(",", ".")
