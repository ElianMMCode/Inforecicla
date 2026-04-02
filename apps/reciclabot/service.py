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

    def generar_contexto_eca(self, punto_eca):
        """
        Extrae todos los datos relevantes del Punto ECA para alimentar al asistente IA.
        Incluye: info general, responsable, ubicación, horario, KPIs, inventario extendido, y resumen operativo.
        """
        from apps.users.models import Usuario
        from apps.operations.models import CompraInventario, VentaInventario
        import datetime

        # -------------------
        # 1. Datos del Punto ECA
        # -------------------
        contexto = f"Información del Punto ECA: {punto_eca.nombre}\n"
        contexto += f"Dirección: {punto_eca.direccion}\n"
        contexto += f"Descripción: {getattr(punto_eca, 'descripcion', '-') or '-'}\n"
        contexto += f"Teléfono: {getattr(punto_eca, 'telefono_punto', '-') or '-'}\n"
        contexto += (
            f"Horario atención: {getattr(punto_eca, 'horario_atencion', '-') or '-'}\n"
        )
        contexto += f"\n"
        # -------------------
        # 2. Responsable/Gestor
        # -------------------
        gestor = getattr(punto_eca, "gestor_eca", None)
        if gestor and isinstance(gestor, Usuario):
            contexto += f"Responsable: {gestor.get_full_name()}\n"
            contexto += (
                f"Email de responsable: {getattr(gestor, 'email', '-') or '-'}\n"
            )
            contexto += (
                f"Celular de responsable: {getattr(gestor, 'celular', '-') or '-'}\n"
            )
        contexto += "\n"

        # -------------------
        # 3. KPIs principales (operativos y de inventario)
        # -------------------
        items = Inventario.objects.filter(punto_eca=punto_eca).select_related(
            "material"
        )
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

        contexto += f"Inventario total: {total_inventario} unidades ({ocupacion_pct}% de capacidad; total máxima: {total_capacidad})\n"
        contexto += f"Cantidad de materiales: {materiales_count}\n"
        contexto += f"Materiales (stock bajo): {materiales_alerta}, (críticos): {materiales_critico}\n"
        contexto += "\n"

        # -------------------
        # 4. Detalle de materiales en inventario
        # -------------------
        contexto += "Inventario detallado por material:\n"
        if not items.exists():
            contexto += "- El inventario está vacío actualmente.\n"
        else:
            for item in items:
                estado = "Óptimo"
                if hasattr(item, "alerta") and item.alerta:
                    if item.alerta == "critico":
                        estado = "Crítico"
                    elif item.alerta == "alerta":
                        estado = "Bajo"
                contexto += (
                    f"- {item.material.nombre}: {item.stock_actual}/{item.capacidad_maxima} {item.unidad_medida}, "
                    f"ocupación: {item.ocupacion_actual}%, precio compra: ${item.precio_compra}, precio venta: ${item.precio_venta} (Estado: {estado})\n"
                )
        contexto += "\n"

        # -------------------
        # 5. KPIs de operaciones: entradas y salidas recientes
        # -------------------
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
        contexto += f"Entradas este mes: {entradas_mes} unidades\n"
        contexto += f"Salidas este mes: {salidas_mes} unidades\n"
        contexto += "\n"

        # 6. Movimientos recientes (últimas 5 operaciones)
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
        # Filtrar movimientos sin fecha válida para evitar errores de ordenación
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
            contexto += "Últimos movimientos:\n"
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

        # -------------------
        # 7. Próximos eventos del calendario del punto ECA
        # -------------------
        contexto += "Calendario de actividades (próximos eventos):\n"
        now = datetime.datetime.now(pytz.UTC)

        # Buscar las próximas 5 instancias de eventos (reales, repetidos o únicos) para este punto
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
            contexto += "(No hay actividades calendarizadas próximas.)\n"
        contexto += "\n"
        # -------------------
        # 8. Centros de Acopio asociados al Punto ECA
        # -------------------
        from apps.ecas.models import CentroAcopio
        from config.constants import Visibilidad

        contexto += "Centros de Acopio asociados:\n"
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

    def generar_datos_resumen(self, punto_eca):
        """
        Genera datos estructurados específicos para el dashboard de resumen.
        Retorna un diccionario con todos los KPIs y datos relevantes.
        """
        from apps.users.models import Usuario
        from apps.operations.models import CompraInventario, VentaInventario
        from apps.ecas.models import CentroAcopio
        from config.constants import Visibilidad
        import datetime

        # -------------------
        # 1. KPIs de Inventario
        # -------------------
        items = Inventario.objects.filter(punto_eca=punto_eca).select_related("material")
        total_inventario = sum(item.stock_actual for item in items)
        total_capacidad = sum(item.capacidad_maxima for item in items)
        ocupacion_pct = round((total_inventario / total_capacidad) * 100, 1) if total_capacidad else 0.0

        materiales_count = items.count()
        materiales_alerta = items.filter(alerta="alerta").count() if hasattr(items, 'filter') else 0
        materiales_critico = items.filter(alerta="critico").count() if hasattr(items, 'filter') else 0

        # -------------------
        # 2. Operaciones del mes
        # -------------------
        ahora = datetime.datetime.now()
        primero_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        entradas_mes = CompraInventario.objects.filter(
            inventario__punto_eca=punto_eca, fecha_compra__gte=primero_mes
        ).aggregate(total_entradas_sum=Sum("cantidad"))["total_entradas_sum"] or 0

        salidas_mes = VentaInventario.objects.filter(
            inventario__punto_eca=punto_eca, fecha_venta__gte=primero_mes
        ).aggregate(total_salidas_sum=Sum("cantidad"))["total_salidas_sum"] or 0

        # -------------------
        # 3. Movimientos recientes (últimos 5)
        # -------------------
        movimientos_entrada = list(CompraInventario.objects.filter(
            inventario__punto_eca=punto_eca
        ).order_by("-fecha_compra")[:3])

        movimientos_salida = list(VentaInventario.objects.filter(
            inventario__punto_eca=punto_eca
        ).order_by("-fecha_venta")[:3])

        # Combinar y ordenar todos los movimientos
        movimientos = []
        for mov in movimientos_entrada:
            if mov.fecha_compra:
                usuario = 'Sistema'
                # Intentar obtener el usuario de diferentes campos posibles
                for campo_usuario in ['creado_por', 'usuario', 'responsable']:
                    if hasattr(mov, campo_usuario):
                        usuario_obj = getattr(mov, campo_usuario, None)
                        if usuario_obj:
                            usuario = usuario_obj.get_full_name() if hasattr(usuario_obj, 'get_full_name') else str(usuario_obj)
                            break

                movimientos.append({
                    'tipo': 'Entrada',
                    'cantidad': mov.cantidad,
                    'material': mov.inventario.material.nombre if mov.inventario and mov.inventario.material else 'Material desconocido',
                    'fecha': mov.fecha_compra,
                    'usuario': usuario,
                    'icono': 'arrow-down-circle',
                    'color': 'text-success'
                })

        for mov in movimientos_salida:
            if mov.fecha_venta:
                usuario = 'Sistema'
                # Intentar obtener el usuario de diferentes campos posibles
                for campo_usuario in ['creado_por', 'usuario', 'responsable']:
                    if hasattr(mov, campo_usuario):
                        usuario_obj = getattr(mov, campo_usuario, None)
                        if usuario_obj:
                            usuario = usuario_obj.get_full_name() if hasattr(usuario_obj, 'get_full_name') else str(usuario_obj)
                            break

                movimientos.append({
                    'tipo': 'Salida',
                    'cantidad': mov.cantidad,
                    'material': mov.inventario.material.nombre if mov.inventario and mov.inventario.material else 'Material desconocido',
                    'fecha': mov.fecha_venta,
                    'usuario': usuario,
                    'icono': 'arrow-up-circle',
                    'color': 'text-warning'
                })

        # Ordenar por fecha más reciente
        movimientos = sorted(movimientos, key=lambda x: x['fecha'], reverse=True)[:5]

        # Formatear movimientos para el template
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

        # -------------------
        # 4. Próximos eventos (próximos 3)
        # -------------------
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
                'tipo': base.tipo_repeticion if hasattr(base, 'tipo_repeticion') and base.tipo_repeticion else 'Único',
                'observaciones': instancia.observaciones or ''
            })

        # -------------------
        # 5. Materiales críticos y alertas
        # -------------------
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

        # -------------------
        # 6. Centros de acopio
        # -------------------
        centros_globales = CentroAcopio.objects.filter(visibilidad=Visibilidad.GLOBAL)
        centros_propios = CentroAcopio.objects.filter(
            puntos_eca=punto_eca, visibilidad=Visibilidad.ECA
        )

        centros_info = {
            'propios': [{'nombre': c.nombre, 'tipo': c.tipo_centro} for c in centros_propios],
            'globales': [{'nombre': c.nombre, 'tipo': c.tipo_centro} for c in centros_globales]
        }

        # -------------------
        # 7. Información del responsable
        # -------------------
        gestor_info = {}
        gestor = getattr(punto_eca, "gestor_eca", None)
        if gestor and isinstance(gestor, Usuario):
            gestor_info = {
                'nombre': gestor.get_full_name(),
                'email': getattr(gestor, 'email', ''),
                'celular': getattr(gestor, 'celular', '')
            }

        return {
            # KPIs principales
            'inventarioTotal': total_inventario,
            'capacidadTotal': total_capacidad,
            'capacidadPorcentaje': ocupacion_pct,
            'entradasMes': entradas_mes,
            'salidasMes': salidas_mes,
            'materialesCount': materiales_count,
            'materialesAlerta': materiales_alerta,
            'materialesCritico': materiales_critico,

            # Datos detallados
            'movimientos': movimientos_formateados,
            'eventosProximos': eventos_proximos,
            'materialesCriticos': materiales_criticos,
            'materialesAlertas': materiales_alertas,
            'centrosAcopio': centros_info,
            'gestor': gestor_info,

            # Información del punto
            'puntoEca': {
                'nombre': punto_eca.nombre,
                'direccion': punto_eca.direccion,
                'descripcion': getattr(punto_eca, 'descripcion', '') or '',
                'telefono': getattr(punto_eca, 'telefono_punto', '') or '',
                'horario': getattr(punto_eca, 'horario_atencion', '') or ''
            }
        }

    def consultar(self, punto_eca, pregunta_usuario):
        # Generar la base de conocimientos en tiempo real
        contexto_real = self.generar_contexto_eca(punto_eca)

        # Prompt de Sistema: Define el comportamiento y los límites
        system_message = {
            "role": "system",
            "content": (
                "Eres el Asistente Virtual de Inforecicla. Tu función es ayudar al gestor del Punto ECA "
                "a entender su inventario y operaciones. "
                f"Solo tienes acceso a los siguientes datos reales: {contexto_real}. "
                "REGLAS: 1. Si te preguntan por datos que no están en el contexto, responde que no tienes acceso. 2. Si te preguntan sobre temas que no sean reciclaje profesional u opciones relacionadas sobre algún material, limita tu respuesta únicamente a ese tema. "
                "2. Sé breve y profesional. 3. No menciones el término 'contexto' al usuario."
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
