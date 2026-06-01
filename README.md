# Finanzas Hogar (Django)

Estructura inicial para una aplicacion de finanzas del hogar.

## Requisitos
- Python 3.13+

## Primer uso
1. Crear y activar entorno virtual
2. Instalar dependencias: `pip install -r requirements.txt`
3. Ejecutar migraciones: `python manage.py migrate`
4. Levantar servidor: `python manage.py runserver`

## Apps incluidas
- `cuentas`: cuentas bancarias, efectivo, tarjetas.
- `categorias`: clasificacion de ingresos y gastos.
- `movimientos`: ingresos, gastos y transferencias.
- `presupuestos`: limites de gasto por categoria y periodo.
- `reportes`: panel general y reportes.
