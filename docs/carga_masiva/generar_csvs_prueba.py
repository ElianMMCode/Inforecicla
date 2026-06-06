"""
Genera los CSV de prueba para la carga masiva.

Reproducible: misma seed produce los mismos archivos.

Uso:
    python3 docs/carga_masiva/generar_csvs_prueba.py
"""
import csv
import random
import datetime
import io
from pathlib import Path

SEED = 20260606

MATERIALES_REALES = [
    "Aceite de cocina usado (UCE)",
    "Acero/Hojalata",
    "Aluminio",
    "Botella PET transparente",
    "Botella PET verde",
    "Botella retornable vidrio",
    "Botellas PET transparentes",
    "Cartón",
    "Cartón corrugado",
    "Chatarra férrica",
    "Envase HDPE (detergente)",
    "Envase PP alimentos",
    "Envase Tetra Pak",
    "Film stretch LDPE",
    "Frasco vidrio ámbar",
    "Frasco vidrio transparente",
    "Frasco vidrio verde",
    "Lata de acero/hojalata",
    "Lata de aluminio",
    "Latas de bebida de aluminio",
    "Papel bond blanco",
    "Papel periódico",
    "Plástico PET",
    "Revistas y mixtos",
    "Ropa de algodón",
    "Ropa de poliéster",
    "Tapa PP",
    "Tetra Pak",
    "Vidrio",
    "Ámbar",
]

MATERIALES_INVENTADOS = [
    "Material NoExistente",
    "Material Inventado 019",
    "Material Nuevo Test",
]

OBSERVACIONES = [
    "Stock bajo",
    "Material reetiquetado",
    "Cambio de calidad",
    "Proveedor habitual",
    "Sin observaciones relevantes",
    "Super oferta",
    "Lote especial",
    "Compra adicional" if "compra" else "Venta adicional",
]

OBSERVACIONES_COMPRA = [
    "Stock bajo",
    "Material reetiquetado",
    "Cambio de calidad",
    "Proveedor habitual",
    "Sin observaciones relevantes",
    "Lote especial",
    "Compra adicional",
    "Reposición mensual",
]

OBSERVACIONES_VENTA = [
    "Cliente habitual",
    "Sin observaciones relevantes",
    "Super oferta",
    "Descuento aplicado",
    "Venta especial",
    "Pedido urgente",
    "Cliente nuevo",
    "Venta adicional",
]


def _elegir_material(tipo):
    """98% real, 2% inventado (para forzar errores de validación)."""
    if random.random() < 0.02:
        return random.choice(MATERIALES_INVENTADOS)
    return random.choice(MATERIALES_REALES)


def _fecha_aleatoria(year, month, day):
    hora = random.randint(6, 21)
    minuto = random.randint(0, 59)
    segundo = random.randint(0, 59)
    return datetime.datetime(year, month, day, hora, minuto, segundo)


def _cantidad():
    return round(random.uniform(5.0, 120.0), 1)


def _precio_compra():
    return round(random.uniform(0.4, 3.5), 2)


def _precio_venta():
    return round(random.uniform(0.5, 5.5), 2)


def generar_csv(tipo, dias, filas_por_dia, year=2026, month=6):
    """
    Genera el CSV. tipo: "compra" o "venta". dias: número de días desde
    el 1 del mes. filas_por_dia: cuántas filas por cada día.
    """
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    if tipo == "compra":
        writer.writerow(
            ["nombreMaterial", "cantidad", "precioCompra", "fechaCompra", "observaciones"]
        )
        campo_precio = "precioCompra"
        campo_fecha = "fechaCompra"
        observaciones_pool = OBSERVACIONES_COMPRA
    else:
        writer.writerow(
            ["nombreMaterial", "cantidad", "precioVenta", "fechaVenta", "observaciones"]
        )
        campo_precio = "precioVenta"
        campo_fecha = "fechaVenta"
        observaciones_pool = OBSERVACIONES_VENTA

    for dia in range(1, dias + 1):
        for _ in range(filas_por_dia):
            fecha = _fecha_aleatoria(year, month, dia)
            if tipo == "compra":
                fila = [
                    _elegir_material("compra"),
                    f"{_cantidad():.1f}",
                    f"{_precio_compra():.2f}",
                    fecha.strftime("%Y-%m-%d %H:%M:%S"),
                    random.choice(observaciones_pool),
                ]
            else:
                fila = [
                    _elegir_material("venta"),
                    f"{_cantidad():.1f}",
                    f"{_precio_venta():.2f}",
                    fecha.strftime("%Y-%m-%d %H:%M:%S"),
                    random.choice(observaciones_pool),
                ]
            writer.writerow(fila)
    return output.getvalue()


def main():
    base = Path(__file__).resolve().parent
    random.seed(SEED)
    compras = generar_csv("compra", dias=30, filas_por_dia=20)
    (base / "test_compras_materiales_masivo.csv").write_text(compras, encoding="utf-8")
    random.seed(SEED + 1)
    ventas = generar_csv("venta", dias=30, filas_por_dia=20)
    (base / "test_ventas_materiales_masivo.csv").write_text(ventas, encoding="utf-8")
    print("OK: 600 filas compras + 600 filas ventas en junio 2026")


if __name__ == "__main__":
    main()
