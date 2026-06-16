from groq import Groq
from django.conf import settings
from apps.inventory.models import Inventario
from django.db.models import Sum
from apps.scheduling.models import EventoInstancia
import pytz


class AsistenteECAService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = (
            "llama-3.1-8b-instant"  # Balance perfecto entre velocidad y razonamiento
        )

    def _contexto_datos_punto(self, punto_eca):
        contexto = f"Informacion del Punto ECA: {punto_eca.nombre}\n"
        contexto += f"Direccion: {punto_eca.direccion}\n"
        contexto += f"Descripcion: {getattr(punto_eca, 'descripcion', '-') or '-'}\n"
        contexto += f"Telefono: {getattr(punto_eca, 'telefono_punto', '-') or '-'}\n"
        contexto += f"Horario atencion: {getattr(punto_eca, 'horario_atencion', '-') or '-'}\n"
        contexto += "\n"
        return contexto

    def _contexto_responsable(self, punto_eca):
        from apps.users.models import Usuario
        contexto = ""
        gestor = getattr(punto_eca, "gestor_eca", None)
        if gestor and isinstance(gestor, Usuario):
            contexto += f"Responsable: {gestor.get_full_name()}\n"
            contexto += f"Email de responsable: {getattr(gestor, 'email', '-') or '-'}\n"
            contexto += f"Celular de responsable: {getattr(gestor, 'celular', '-') or '-'}\n"
        contexto += "\n"
        return contexto

    def _contexto_kpis(self, punto_eca):
        items = Inventario.objects.filter(punto_eca=punto_eca).select_related("material")
        total_inventario = sum(item.stock_actual for item in items)
        total_capacidad = sum(item.capacidad_maxima for item in items)
        ocupacion_pct = (
            round((total_inventario / total_capacidad) * 100, 1)
            if total_capacidad
            else 0.0
        )
        materiales_count = items.count()
        materiales_alerta = (
            items.filter(alerta="alerta").count() if hasattr(items, "filter") else 0
        )
        materiales_critico = (
            items.filter(alerta="critico").count() if hasattr(items, "filter") else 0
        )
        contexto = f"Inventario total: {total_inventario} unidades ({ocupacion_pct}% de capacidad; total maxima: {total_capacidad})\n"
        contexto += f"Cantidad de materiales: {materiales_count}\n"
        contexto += f"Materiales (por llenarse): {materiales_alerta}, (llenos): {materiales_critico}\n"
        contexto += "\n"
        return contexto, items

    def _contexto_inventario_detallado(self, items):
        contexto = "Inventario detallado por material:\n"
        if not items.exists():
            contexto += "- El inventario esta vacio actualmente.\n"
        else:
            for item in items:
                estado = "Disponible"
                if hasattr(item, "alerta") and item.alerta:
                    if item.alerta == "critico":
                        estado = "Critico"
                    elif item.alerta == "alerta":
                        estado = "Por llenarse"
                contexto += (
                    f"- {item.material.nombre}: {item.stock_actual}/{item.capacidad_maxima} {item.unidad_medida}, "
                    f"ocupacion: {item.ocupacion_actual}%, precio compra: ${item.precio_compra}, precio venta: ${item.precio_venta} (Estado: {estado})\n"
                )
        contexto += "\n"
        return contexto

    def _contexto_operaciones_mes(self, punto_eca):
        from apps.operations.models import CompraInventario, VentaInventario
        import datetime
        ahora = datetime.datetime.now()
        primero_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        entradas_mes = (
            CompraInventario.objects.filter(
                inventario__punto_eca=punto_eca, fecha_compra__gte=primero_mes
            ).aggregate(total_entradas_sum=Sum("cantidad"))["total_entradas_sum"]
            or 0
        )
        salidas_mes = (
            VentaInventario.objects.filter(
                inventario__punto_eca=punto_eca, fecha_venta__gte=primero_mes
            ).aggregate(total_salidas_sum=Sum("cantidad"))["total_salidas_sum"]
            or 0
        )
        contexto = f"Entradas este mes: {entradas_mes} unidades\n"
        contexto += f"Salidas este mes: {salidas_mes} unidades\n"
        contexto += "\n"
        return contexto

    def _contexto_movimientos(self, punto_eca):
        from apps.operations.models import CompraInventario, VentaInventario
        contexto = ""
        movimientos = list(
            CompraInventario.objects.filter(inventario__punto_eca=punto_eca).order_by(
                "-fecha_compra"
            )[:3]
        )
        movimientos += list(
            VentaInventario.objects.filter(inventario__punto_eca=punto_eca).order_by(
                "-fecha_venta"
            )[:3]
        )
        movimientos = [
            mv
            for mv in movimientos
            if (getattr(mv, "fecha_compra", None) or getattr(mv, "fecha_venta", None))
        ]
        movimientos = sorted(
            movimientos,
            key=lambda mv: (
                getattr(mv, "fecha_compra", None)
                or getattr(mv, "fecha_venta", None)
                or ""
            ),
            reverse=True,
        )[:5]
        if movimientos:
            contexto += "Ultimos movimientos:\n"
            for mov in movimientos:
                tipo = "Entrada" if isinstance(mov, CompraInventario) else "Salida"
                fecha = getattr(mov, "fecha_compra", getattr(mov, "fecha_venta", "-"))
                cantidad = getattr(mov, "cantidad", "-")
                mat = getattr(mov, "inventario", None)
                mat_nombre = (
                    mat.material.nombre
                    if mat and hasattr(mat, "material") and mat.material
                    else "-"
                )
                contexto += f"- {tipo}: {mat_nombre}, {cantidad} unidades, {fecha}\n"
            contexto += "\n"
        return contexto

    def _contexto_eventos(self, punto_eca):
        import datetime
        contexto = "Calendario de actividades (proximos eventos):\n"
        now = datetime.datetime.now(pytz.UTC)
        instancias_proximas = EventoInstancia.objects.filter(
            punto_eca=punto_eca, fecha_inicio__gte=now
        ).order_by("fecha_inicio")[:5]
        if instancias_proximas:
            for instancia in instancias_proximas:
                base = instancia.evento_base
                tipo = (
                    base.tipo_repeticion
                    if hasattr(base, "tipo_repeticion") and base.tipo_repeticion
                    else "--"
                )
                contexto += f"- {base.titulo or 'Evento'}: {instancia.fecha_inicio.strftime('%d/%m/%Y %H:%M')} - {instancia.fecha_fin.strftime('%d/%m/%Y %H:%M') if instancia.fecha_fin else ''} | Tipo: {tipo}"
                if instancia.observaciones:
                    contexto += f" | Observaciones: {instancia.observaciones}"
                contexto += "\n"
        else:
            contexto += "(No hay actividades calendarizadas proximas.)\n"
        contexto += "\n"
        return contexto

    def _contexto_centros(self, punto_eca):
        from apps.ecas.models import CentroAcopio
        from config.constants import Visibilidad
        contexto = "Centros de Acopio asociados:\n"
        centros_globales = CentroAcopio.objects.filter(visibilidad=Visibilidad.GLOBAL)
        centros_propios = CentroAcopio.objects.filter(
            puntos_eca=punto_eca, visibilidad=Visibilidad.ECA
        )
        if centros_propios.exists():
            contexto += "- Propios/Local: "
            for c in centros_propios:
                contexto += f"{c.nombre} (Tipo: {c.tipo_centro}) | "
            contexto = contexto.rstrip(" | ") + "\n"
        else:
            contexto += "- Propios/Local: Ninguno\n"
        if centros_globales.exists():
            contexto += "- Globales: "
            for c in centros_globales:
                contexto += f"{c.nombre} (Tipo: {c.tipo_centro}) | "
            contexto = contexto.rstrip(" | ") + "\n"
        else:
            contexto += "- Globales: Ninguno\n"
        contexto += "\n"
        return contexto

    def generar_contexto_eca(self, punto_eca):
        contexto = self._contexto_datos_punto(punto_eca)
        contexto += self._contexto_responsable(punto_eca)
        kpis, items = self._contexto_kpis(punto_eca)
        contexto += kpis
        contexto += self._contexto_inventario_detallado(items)
        contexto += self._contexto_operaciones_mes(punto_eca)
        contexto += self._contexto_movimientos(punto_eca)
        contexto += self._contexto_eventos(punto_eca)
        contexto += self._contexto_centros(punto_eca)
        return contexto

    def _kpis_inventario(self, punto_eca):
        items = Inventario.objects.filter(punto_eca=punto_eca).select_related("material")
        if not items.exists():
            total_inventario = 0
            total_capacidad = 0
            ocupacion_pct = 0.0
            materiales_count = 0
            materiales_alerta = 0
            materiales_critico = 0
        else:
            total_inventario = sum(item.stock_actual for item in items)
            total_capacidad = sum(item.capacidad_maxima for item in items)
            ocupacion_pct = round((total_inventario / total_capacidad) * 100, 1) if total_capacidad else 0.0
            materiales_count = items.count()
            materiales_alerta = items.filter(alerta="alerta").count() if hasattr(items, 'filter') else 0
            materiales_critico = items.filter(alerta="critico").count() if hasattr(items, 'filter') else 0
        return items, total_inventario, total_capacidad, ocupacion_pct, materiales_count, materiales_alerta, materiales_critico

    def _operaciones_del_mes(self, punto_eca, primero_mes):
        from apps.operations.models import CompraInventario, VentaInventario
        from django.db.models import Sum
        entradas_mes = CompraInventario.objects.filter(
            inventario__punto_eca=punto_eca, fecha_compra__gte=primero_mes
        ).aggregate(total_entradas_sum=Sum("cantidad"))["total_entradas_sum"] or 0
        salidas_mes = VentaInventario.objects.filter(
            inventario__punto_eca=punto_eca, fecha_venta__gte=primero_mes
        ).aggregate(total_salidas_sum=Sum("cantidad"))["total_salidas_sum"] or 0
        return entradas_mes, salidas_mes

    @staticmethod
    def _obtener_usuario_operacion(mov):
        for campo_usuario in ['creado_por', 'usuario', 'responsable']:
            if hasattr(mov, campo_usuario):
                usuario_obj = getattr(mov, campo_usuario, None)
                if usuario_obj:
                    return usuario_obj.get_full_name() if hasattr(usuario_obj, 'get_full_name') else str(usuario_obj)
        return 'Sistema'

    @staticmethod
    def _procesar_movimientos_entrada(qs_entrada, tipo, fecha_attr, icono, color):
        movimientos = []
        for mov in qs_entrada:
            fecha = getattr(mov, fecha_attr, None)
            if not fecha:
                continue
            movimientos.append({
                'tipo': tipo,
                'cantidad': mov.cantidad,
                'material': mov.inventario.material.nombre if mov.inventario and mov.inventario.material else 'Material desconocido',
                'fecha': fecha,
                'usuario': AsistenteECAService._obtener_usuario_operacion(mov),
                'icono': icono,
                'color': color,
            })
        return movimientos

    def _movimientos_recientes(self, punto_eca):
        from apps.operations.models import CompraInventario, VentaInventario
        movimientos = (
            AsistenteECAService._procesar_movimientos_entrada(
                CompraInventario.objects.filter(
                    inventario__punto_eca=punto_eca
                ).order_by("-fecha_compra")[:3],
                'Entrada', 'fecha_compra', 'arrow-down-circle', 'text-success'
            )
            + AsistenteECAService._procesar_movimientos_entrada(
                VentaInventario.objects.filter(
                    inventario__punto_eca=punto_eca
                ).order_by("-fecha_venta")[:3],
                'Salida', 'fecha_venta', 'arrow-up-circle', 'text-warning'
            )
        )
        movimientos = sorted(movimientos, key=lambda x: x['fecha'], reverse=True)[:5]
        movimientos_formateados = []
        for mov in movimientos:
            movimientos_formateados.append({
                'tipo': mov['tipo'],
                'cantidad': mov['cantidad'],
                'descripcion': mov['material'],
                'usuario': mov['usuario'],
                'fecha': mov['fecha'].isoformat() if hasattr(mov['fecha'], 'isoformat') else str(mov['fecha']),
                'icono': mov['icono'],
                'color': mov['color']
            })
        return movimientos_formateados

    def _eventos_proximos(self, punto_eca):
        import datetime
        now = datetime.datetime.now(pytz.UTC)
        instancias_proximas = EventoInstancia.objects.filter(
            punto_eca=punto_eca, fecha_inicio__gte=now
        ).order_by("fecha_inicio")[:3]
        eventos_proximos = []
        for instancia in instancias_proximas:
            base = instancia.evento_base
            eventos_proximos.append({
                'titulo': base.titulo or 'Evento',
                'fecha_inicio': instancia.fecha_inicio.isoformat(),
                'fecha_fin': instancia.fecha_fin.isoformat() if instancia.fecha_fin else None,
                'tipo': base.tipo_repeticion if hasattr(base, 'tipo_repeticion') and base.tipo_repeticion else 'Unico',
                'observaciones': instancia.observaciones or ''
            })
        return eventos_proximos

    def _materiales_criticos_y_alertas(self, items):
        materiales_criticos = []
        materiales_alertas = []
        for item in items:
            material_info = {
                'nombre': item.material.nombre,
                'stock_actual': item.stock_actual,
                'capacidad_maxima': item.capacidad_maxima,
                'ocupacion': item.ocupacion_actual,
                'unidad': item.unidad_medida
            }
            if hasattr(item, 'alerta'):
                if item.alerta == 'critico':
                    materiales_criticos.append(material_info)
                elif item.alerta == 'alerta':
                    materiales_alertas.append(material_info)
        return materiales_criticos, materiales_alertas

    def _centros_acopio_data(self, punto_eca):
        from apps.ecas.models import CentroAcopio
        from config.constants import Visibilidad
        centros_globales = CentroAcopio.objects.filter(visibilidad=Visibilidad.GLOBAL)
        centros_propios = CentroAcopio.objects.filter(
            puntos_eca=punto_eca, visibilidad=Visibilidad.ECA
        )

        def _centro_to_dict(c):
            ciudad = ""
            if getattr(c, "ciudad", None):
                ciudad = str(c.ciudad)
            localidad = ""
            if getattr(c, "localidad", None):
                localidad = str(c.localidad)
            return {
                "nombre": c.nombre,
                "tipo": c.tipo_centro,
                "descripcion": getattr(c, "descripcion", "") or "",
                "direccion": getattr(c, "direccion", "") or "",
                "ciudad": ciudad,
                "localidad": localidad,
                "email": getattr(c, "email", "") or "",
                "celular": getattr(c, "celular", "") or "",
                "horario": getattr(c, "horario_atencion", "") or "",
                "sitio_web": getattr(c, "sitio_web", "") or "",
            }

        return {
            "propios": [_centro_to_dict(c) for c in centros_propios],
            "globales": [_centro_to_dict(c) for c in centros_globales],
        }

    def _gestor_data(self, punto_eca):
        from apps.users.models import Usuario
        gestor_info = {}
        gestor = getattr(punto_eca, "gestor_eca", None)
        if gestor and isinstance(gestor, Usuario):
            gestor_info = {
                'nombre': gestor.get_full_name(),
                'email': getattr(gestor, 'email', ''),
                'celular': getattr(gestor, 'celular', '')
            }
        return gestor_info

    def _valor_total_inventario(self, items):
        valor_total_inventario = 0.0
        for item in items:
            precio = item.precio_compra or 0
            if item.stock_actual and precio:
                valor_total_inventario += float(item.stock_actual) * float(precio)
        return round(valor_total_inventario, 2)

    def _calcular_salud(self, materiales_critico, materiales_alerta, total_inventario, total_capacidad):
        if materiales_critico > 0 or (total_capacidad and (float(total_inventario) / float(total_capacidad)) > 0.9):
            return "CRITICO"
        elif materiales_alerta > 0 or (total_capacidad and (float(total_inventario) / float(total_capacidad)) > 0.7):
            return "ATENCION"
        return "OK"

    def _comparativa_mes_anterior(self, punto_eca, primero_mes, entradas_mes, salidas_mes):
        from apps.operations.models import CompraInventario, VentaInventario
        from django.db.models import Sum
        import datetime
        ultimo_dia_mes_anterior_dt = primero_mes - datetime.timedelta(seconds=1)
        primer_dia_mes_anterior_dt = ultimo_dia_mes_anterior_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        entradas_mes_anterior = CompraInventario.objects.filter(
            inventario__punto_eca=punto_eca,
            fecha_compra__gte=primer_dia_mes_anterior_dt,
            fecha_compra__lt=primero_mes,
        ).aggregate(total=Sum("cantidad"))["total"] or 0
        salidas_mes_anterior = VentaInventario.objects.filter(
            inventario__punto_eca=punto_eca,
            fecha_venta__gte=primer_dia_mes_anterior_dt,
            fecha_venta__lt=primero_mes,
        ).aggregate(total=Sum("cantidad"))["total"] or 0
        entradas_mes_f = float(entradas_mes)
        salidas_mes_f = float(salidas_mes)
        entradas_mes_anterior_f = float(entradas_mes_anterior)
        salidas_mes_anterior_f = float(salidas_mes_anterior)
        if entradas_mes_anterior_f > 0:
            variacion_entradas = round(((entradas_mes_f - entradas_mes_anterior_f) / entradas_mes_anterior_f) * 100, 1)
        elif entradas_mes_f > 0:
            variacion_entradas = 100.0
        else:
            variacion_entradas = 0.0
        if salidas_mes_anterior_f > 0:
            variacion_salidas = round(((salidas_mes_f - salidas_mes_anterior_f) / salidas_mes_anterior_f) * 100, 1)
        elif salidas_mes_f > 0:
            variacion_salidas = 100.0
        else:
            variacion_salidas = 0.0
        return {
            'entradas': entradas_mes_anterior,
            'salidas': salidas_mes_anterior,
            'variacionEntradas': variacion_entradas,
            'variacionSalidas': variacion_salidas,
        }

    def _transacciones_y_balance(self, punto_eca, primero_mes, entradas_mes_f, salidas_mes_f):
        from apps.operations.models import CompraInventario, VentaInventario
        transacciones_mes = (
            CompraInventario.objects.filter(
                inventario__punto_eca=punto_eca, fecha_compra__gte=primero_mes
            ).count()
            + VentaInventario.objects.filter(
                inventario__punto_eca=punto_eca, fecha_venta__gte=primero_mes
            ).count()
        )
        balance_neto_mes = round(entradas_mes_f - salidas_mes_f, 2)
        return transacciones_mes, balance_neto_mes

    def _top_materiales_mes(self, punto_eca, primero_mes):
        from apps.operations.models import CompraInventario, VentaInventario
        from collections import defaultdict
        materiales_mov = defaultdict(lambda: {"kg": 0.0, "movimientos": 0})
        for mov in CompraInventario.objects.filter(
            inventario__punto_eca=punto_eca, fecha_compra__gte=primero_mes
        ).select_related("inventario__material"):
            mat_nombre = (
                mov.inventario.material.nombre
                if mov.inventario and mov.inventario.material
                else "Desconocido"
            )
            materiales_mov[mat_nombre]["kg"] += float(mov.cantidad)
            materiales_mov[mat_nombre]["movimientos"] += 1
        for mov in VentaInventario.objects.filter(
            inventario__punto_eca=punto_eca, fecha_venta__gte=primero_mes
        ).select_related("inventario__material"):
            mat_nombre = (
                mov.inventario.material.nombre
                if mov.inventario and mov.inventario.material
                else "Desconocido"
            )
            materiales_mov[mat_nombre]["kg"] += float(mov.cantidad)
            materiales_mov[mat_nombre]["movimientos"] += 1
        return [
            {
                "nombre": nombre,
                "movimientos": data["movimientos"],
                "totalKg": round(data["kg"], 2),
            }
            for nombre, data in sorted(
                materiales_mov.items(), key=lambda x: x[1]["kg"], reverse=True
            )[:3]
        ]

    def _tendencia_diaria_7d(self, punto_eca, ahora):
        from apps.operations.models import CompraInventario, VentaInventario
        import datetime
        inicio_7d = (ahora - datetime.timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        dias_dict = {}
        for i in range(7):
            dia = inicio_7d + datetime.timedelta(days=i)
            dias_dict[dia.date().isoformat()] = {
                "fecha": dia.date().isoformat(),
                "entradas": 0.0,
                "salidas": 0.0,
            }
        for mov in CompraInventario.objects.filter(
            inventario__punto_eca=punto_eca, fecha_compra__gte=inicio_7d
        ):
            clave = mov.fecha_compra.date().isoformat()
            if clave in dias_dict:
                dias_dict[clave]["entradas"] += float(mov.cantidad)
        for mov in VentaInventario.objects.filter(
            inventario__punto_eca=punto_eca, fecha_venta__gte=inicio_7d
        ):
            clave = mov.fecha_venta.date().isoformat()
            if clave in dias_dict:
                dias_dict[clave]["salidas"] += float(mov.cantidad)
        return [
            {
                "fecha": d["fecha"],
                "entradas": round(d["entradas"], 2),
                "salidas": round(d["salidas"], 2),
            }
            for d in dias_dict.values()
        ]

    def _distribucion_categorias(self, items):
        from collections import defaultdict
        categorias_dict = defaultdict(lambda: {"items": 0, "kg": 0.0})
        for item in items:
            cat_nombre = "Sin categoria"
            if item.material and getattr(item.material, "categoria", None):
                cat_nombre = item.material.categoria.nombre
            categorias_dict[cat_nombre]["items"] += 1
            categorias_dict[cat_nombre]["kg"] += float(item.stock_actual)
        total_kg_cats = sum(c["kg"] for c in categorias_dict.values())
        categoria_breakdown = []
        for nombre, data in categorias_dict.items():
            pct = round((data["kg"] / total_kg_cats) * 100, 1) if total_kg_cats else 0.0
            categoria_breakdown.append(
                {
                    "nombre": nombre,
                    "items": data["items"],
                    "kg": round(data["kg"], 2),
                    "porcentaje": pct,
                }
            )
        categoria_breakdown.sort(key=lambda x: x["porcentaje"], reverse=True)
        return categoria_breakdown

    def _dias_desde_ultimo_movimiento(self, punto_eca, ahora):
        from apps.operations.models import CompraInventario, VentaInventario
        ultima_compra_dt = CompraInventario.objects.filter(
            inventario__punto_eca=punto_eca
        ).order_by("-fecha_compra").values_list("fecha_compra", flat=True).first()
        ultima_venta_dt = VentaInventario.objects.filter(
            inventario__punto_eca=punto_eca
        ).order_by("-fecha_venta").values_list("fecha_venta", flat=True).first()
        candidatos = [d for d in (ultima_compra_dt, ultima_venta_dt) if d is not None]
        if candidatos:
            ultimo_mov_dt = max(candidatos)
            if ultimo_mov_dt.tzinfo is None:
                ultimo_mov_dt = pytz.UTC.localize(ultimo_mov_dt)
            if ahora.tzinfo is None:
                ahora_tz = pytz.UTC.localize(ahora)
            else:
                ahora_tz = ahora
            return (ahora_tz - ultimo_mov_dt).days
        return None

    def _punto_eca_info(self, punto_eca):
        return {
            'nombre': punto_eca.nombre,
            'direccion': punto_eca.direccion,
            'descripcion': getattr(punto_eca, 'descripcion', '') or '',
            'telefono': getattr(punto_eca, 'telefono_punto', '') or '',
            'horario': getattr(punto_eca, 'horario_atencion', '') or ''
        }

    def generar_datos_resumen(self, punto_eca):
        """
        Genera datos estructurados especificos para el dashboard de resumen.
        Retorna un diccionario con todos los KPIs y datos relevantes.
        """
        import datetime

        items, total_inventario, total_capacidad, ocupacion_pct, materiales_count, materiales_alerta, materiales_critico = self._kpis_inventario(punto_eca)

        ahora = datetime.datetime.now()
        primero_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        entradas_mes, salidas_mes = self._operaciones_del_mes(punto_eca, primero_mes)
        entradas_mes_f = float(entradas_mes)
        salidas_mes_f = float(salidas_mes)

        movimientos_formateados = self._movimientos_recientes(punto_eca)
        eventos_proximos = self._eventos_proximos(punto_eca)
        materiales_criticos, materiales_alertas = self._materiales_criticos_y_alertas(items)
        centros_info = self._centros_acopio_data(punto_eca)
        gestor_info = self._gestor_data(punto_eca)
        valor_total_inventario = self._valor_total_inventario(items)
        salud_punto = self._calcular_salud(materiales_critico, materiales_alerta, total_inventario, total_capacidad)
        mes_anterior = self._comparativa_mes_anterior(punto_eca, primero_mes, entradas_mes, salidas_mes)
        transacciones_mes, balance_neto_mes = self._transacciones_y_balance(punto_eca, primero_mes, entradas_mes_f, salidas_mes_f)
        top_materiales = self._top_materiales_mes(punto_eca, primero_mes)
        tendencia_diaria = self._tendencia_diaria_7d(punto_eca, ahora)
        categoria_breakdown = self._distribucion_categorias(items)
        dias_ultimo_movimiento = self._dias_desde_ultimo_movimiento(punto_eca, ahora)
        punto_eca_info = self._punto_eca_info(punto_eca)

        ultima_actualizacion = datetime.datetime.now().isoformat()

        import logging
        logging.warning(f"RESUMEN puntoECA={punto_eca.pk if hasattr(punto_eca,'pk') else punto_eca} KPIs: inventarioTotal={total_inventario}, capacidadTotal={total_capacidad}, ocupacion_pct={ocupacion_pct}, entradasMes={entradas_mes}, salidasMes={salidas_mes}, materialesCount={materiales_count}, materialesAlerta={materiales_alerta}, materialesCritico={materiales_critico}")
        logging.warning(f"MOVIMIENTOS: {movimientos_formateados}")
        logging.warning(f"INVENTARIO ITEMS: {[{'nombre': i.material.nombre, 'stock': i.stock_actual, 'capacidad': i.capacidad_maxima} for i in items]}")
        logging.warning(f"RESUMEN datos criticos={len(materiales_criticos)}, alertas={len(materiales_alertas)} materialesCriticos={materiales_criticos} materialesAlertas={materiales_alertas}")

        return {
            'inventarioTotal': total_inventario,
            'capacidadTotal': total_capacidad,
            'capacidadPorcentaje': ocupacion_pct,
            'entradasMes': entradas_mes,
            'salidasMes': salidas_mes,
            'materialesCount': materiales_count,
            'materialesAlerta': materiales_alerta,
            'materialesCritico': materiales_critico,
            'valorTotalInventario': valor_total_inventario,
            'transaccionesMes': transacciones_mes,
            'balanceNetoMes': balance_neto_mes,
            'saludPunto': salud_punto,
            'mesAnterior': mes_anterior,
            'movimientos': movimientos_formateados,
            'eventosProximos': eventos_proximos,
            'materialesCriticos': materiales_criticos,
            'materialesAlertas': materiales_alertas,
            'centrosAcopio': centros_info,
            'gestor': gestor_info,
            'topMateriales': top_materiales,
            'tendenciaDiaria': tendencia_diaria,
            'categoriaBreakdown': categoria_breakdown,
            'diasUltimoMovimiento': dias_ultimo_movimiento,
            'ultimaActualizacion': ultima_actualizacion,
            'puntoEca': punto_eca_info,
        }

    def consultar(self, punto_eca, pregunta_usuario):
        # Generar la base de conocimientos en tiempo real
        contexto_real = self.generar_contexto_eca(punto_eca)

        # Prompt de Sistema: Define el comportamiento y los limites
        system_message = {
            "role": "system",
            "content": (
                "Eres el Asistente Virtual de Inforecicla. Tu funcion es ayudar al gestor del Punto ECA "
                "a entender su inventario y operaciones. "
                f"Solo tienes acceso a los siguientes datos reales: {contexto_real}. "
                "REGLAS: 1. Si te preguntan por datos que no estan en el contexto, responde que no tienes acceso. 2. Si te preguntan sobre temas que no sean reciclaje profesional u opciones relacionadas sobre algun material, limita tu respuesta unicamente a ese tema. "
                "2. Se breve y profesional. 3. No menciones el termino 'contexto' al usuario."
            ),
        }

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_message["content"]},
                    {"role": "user", "content": pregunta_usuario},
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=500,
            )
            return chat_completion.choices[0].message.content
        except Exception:
            # Si ocurre un error con la API, devolvemos un mensaje amigable
            return "Lo siento, hubo un problema al consultar la IA. Intentalo otra vez o contacta al soporte."
