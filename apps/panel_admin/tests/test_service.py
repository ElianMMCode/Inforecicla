from django.test import TestCase
from apps.panel_admin.service import AdminPuntoECAService


class AdminPuntoECAServiceTest(TestCase):
    """Tests for AdminPuntoECAService data methods."""

    def test_obtener_puntos_dashboard_returns_list(self):
        """Empty DB should return empty list, not error."""
        puntos = AdminPuntoECAService.obtener_puntos_dashboard()
        self.assertIsInstance(puntos, list)
        self.assertEqual(len(puntos), 0)

    def test_obtener_puntos_dashboard_keys(self):
        """Verify cada punto tiene las claves esperadas por el JS."""
        puntos = AdminPuntoECAService.obtener_puntos_dashboard()
        for p in puntos:
            for key in (
                "id", "nombre", "direccion", "localidad", "gestor",
                "estado", "invEstado", "stockTotal", "capMax",
                "lat", "lng", "compras", "ventas", "margen",
                "msgs", "fecha_creacion",
            ):
                self.assertIn(key, p)

    def test_obtener_historial_returns_list(self):
        """Empty DB should return empty list."""
        items = AdminPuntoECAService.obtener_historial()
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 0)

    def test_obtener_historial_default_6_months(self):
        """Verificar que acepta el parametro meses sin error."""
        items = AdminPuntoECAService.obtener_historial(meses=3)
        self.assertEqual(len(items), 0)

    def test_obtener_historial_keys(self):
        """Verificar claves del historial."""
        items = AdminPuntoECAService.obtener_historial()
        for h in items:
            for key in ("fecha", "tipo", "mat", "kg", "valor", "puntoId"):
                self.assertIn(key, h)

    def test_obtener_eventos_returns_list(self):
        """Eventos vacios."""
        eventos = AdminPuntoECAService.obtener_eventos()
        self.assertIsInstance(eventos, list)
        self.assertEqual(len(eventos), 0)

    def test_obtener_eventos_keys(self):
        """Verificar claves de eventos."""
        eventos = AdminPuntoECAService.obtener_eventos()
        for e in eventos:
            for key in ("fecha", "titulo", "tipo", "es_completado", "puntoId"):
                self.assertIn(key, e)

    def test_obtener_conversaciones_returns_list(self):
        """Conversaciones vacias."""
        convs = AdminPuntoECAService.obtener_conversaciones()
        self.assertIsInstance(convs, list)

    def test_obtener_conversaciones_keys(self):
        """Verificar claves de conversaciones."""
        convs = AdminPuntoECAService.obtener_conversaciones()
        for c in convs:
            for key in ("punto", "ciudadano", "fecha", "msgs", "ultimo", "puntoId"):
                self.assertIn(key, c)

    def test_obtener_usuarios_admin_returns_list(self):
        """Usuarios desde DB vacia."""
        users = AdminPuntoECAService.obtener_usuarios_admin()
        self.assertIsInstance(users, list)

    def test_obtener_usuarios_admin_keys(self):
        """Verificar claves de usuarios."""
        users = AdminPuntoECAService.obtener_usuarios_admin()
        for u in users:
            for key in ("id", "username", "rol", "fecha_registro", "puntos_asignados", "localidad"):
                self.assertIn(key, u)

    def test_obtener_kpis_returns_dict(self):
        """KPIs globales dict con estructura esperada."""
        kpis = AdminPuntoECAService.obtener_kpis(puntos=[])
        self.assertIsInstance(kpis, dict)
        for key in (
            "total_puntos", "activos", "inactivos", "ocupacion_pct",
            "capacidad_pct", "flujo_in", "flujo_out", "compras_total",
            "ventas_total", "ganancia", "margen_pct", "msgs_sin_resp",
            "deltas", "puntos_por_gestor", "top_materiales",
        ):
            self.assertIn(key, kpis)

    def test_obtener_kpis_empty_defaults(self):
        """Sin puntos todos los valores deben ser 0."""
        kpis = AdminPuntoECAService.obtener_kpis(puntos=[])
        self.assertEqual(kpis["total_puntos"], 0)
        self.assertEqual(kpis["activos"], 0)
        self.assertEqual(kpis["ganancia"], 0)
        self.assertEqual(kpis["margen_pct"], 0)
        self.assertEqual(kpis["puntos_por_gestor"], [])

    def test_obtener_inventario_desglosado_returns_list(self):
        """Inventario vacio."""
        items = AdminPuntoECAService.obtener_inventario_desglosado()
        self.assertIsInstance(items, list)

    def test_obtener_inventario_desglosado_keys(self):
        """Verificar claves de invData."""
        items = AdminPuntoECAService.obtener_inventario_desglosado()
        for i in items:
            for key in (
                "puntoId", "mat", "stock", "cap", "compra", "venta",
                "cat", "estado", "ultimoMov", "comprasKg", "ventasKg",
            ):
                self.assertIn(key, i)

    def test_inferir_tipo_evento(self):
        """Eventos tipos inferidos."""
        self.assertEqual(AdminPuntoECAService._inferir_tipo_evento("Recoleccion de plastico"), "Recoleccion")
        self.assertEqual(AdminPuntoECAService._inferir_tipo_evento("Entrega de vidrio"), "Recoleccion")
        self.assertEqual(AdminPuntoECAService._inferir_tipo_evento("Mantenimiento de maquina"), "Mantenimiento")
        self.assertEqual(AdminPuntoECAService._inferir_tipo_evento("Taller de capacitacion"), "Capacitacion")
        self.assertEqual(AdminPuntoECAService._inferir_tipo_evento("Inspeccion de bodega"), "Inspeccion")
        self.assertEqual(AdminPuntoECAService._inferir_tipo_evento("Evento general"), "General")

    def test_agrupar_por_gestor_empty(self):
        """Sin puntos retorna lista vacia."""
        result = AdminPuntoECAService._agrupar_por_gestor([])
        self.assertEqual(result, [])

    def test_top_materiales_empty(self):
        """Sin materiales retorna lista vacia."""
        result = AdminPuntoECAService._top_materiales()
        self.assertIsInstance(result, list)
