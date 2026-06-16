from django.test import TestCase
from django.contrib.auth import get_user_model
from .factories import UserFactory, DashboardFactory, WidgetFactory, ReportFactory
from ..models import Dashboard, Widget, Report

User = get_user_model()

class UserModelTest(TestCase):
    """Test cases for User model"""
    
    def test_user_creation(self):
        """Test creating a user"""
        user = UserFactory()
        self.assertTrue(user.email)
        self.assertTrue(user.nombres)
        self.assertTrue(user.apellidos)
        self.assertTrue(user.is_active)
        
    def test_user_str_representation(self):
        """Test string representation of user"""
        user = UserFactory()
        expected = f"{user.nombres} {user.apellidos} - {user.email}"
        self.assertEqual(str(user), expected)

class DashboardModelTest(TestCase):
    """Test cases for Dashboard model"""
    
    def test_dashboard_creation(self):
        """Test creating a dashboard"""
        dashboard = DashboardFactory()
        self.assertTrue(dashboard.nombre)
        self.assertTrue(dashboard.descripcion)
        self.assertIsInstance(dashboard.es_publico, bool)
        self.assertIsNotNone(dashboard.propietario)
        
    def test_dashboard_str_representation(self):
        """Test string representation of dashboard"""
        dashboard = DashboardFactory(nombre='Test Dashboard')
        self.assertEqual(str(dashboard), 'Test Dashboard')
        
    def test_dashboard_owner_relationship(self):
        """Test dashboard owner relationship"""
        user = UserFactory()
        dashboard = DashboardFactory(propietario=user)
        self.assertEqual(dashboard.propietario, user)
        self.assertIn(dashboard, user.dashboards.all())

class WidgetModelTest(TestCase):
    """Test cases for Widget model"""
    
    def test_widget_creation(self):
        """Test creating a widget"""
        widget = WidgetFactory()
        self.assertTrue(widget.titulo)
        self.assertIn(widget.tipo_widget, ['chart', 'table', 'metric', 'text'])
        self.assertGreaterEqual(widget.posicion_x, 0)
        self.assertLessEqual(widget.posicion_x, 11)
        self.assertGreaterEqual(widget.posicion_y, 0)
        self.assertLessEqual(widget.posicion_y, 10)
        self.assertGreaterEqual(widget.ancho, 1)
        self.assertLessEqual(widget.ancho, 4)
        self.assertGreaterEqual(widget.alto, 1)
        self.assertLessEqual(widget.alto, 3)
        self.assertIsNotNone(widget.dashboard)
        
    def test_widget_str_representation(self):
        """Test string representation of widget"""
        widget = WidgetFactory(titulo='Test Widget')
        self.assertEqual(str(widget), 'Test Widget')
        
    def test_widget_dashboard_relationship(self):
        """Test widget dashboard relationship"""
        dashboard = DashboardFactory()
        widget = WidgetFactory(dashboard=dashboard)
        self.assertEqual(widget.dashboard, dashboard)
        self.assertIn(widget, dashboard.widgets.all())

class ReportModelTest(TestCase):
    """Test cases for Report model"""
    
    def test_report_creation(self):
        """Test creating a report"""
        report = ReportFactory()
        self.assertTrue(report.titulo)
        self.assertTrue(report.descripcion)
        self.assertIn(report.tipo_informe, ['sales', 'inventory', 'users', 'operations'])
        self.assertIsNotNone(report.generado_por)
        self.assertIsInstance(report.parametros, dict)
        self.assertIsInstance(report.es_programado, bool)
        
    def test_report_str_representation(self):
        """Test string representation of report"""
        report = ReportFactory(titulo='Test Report')
        self.assertEqual(str(report), 'Test Report')
        
    def test_report_generator_relationship(self):
        """Test report generator relationship"""
        user = UserFactory()
        report = ReportFactory(generado_por=user)
        self.assertEqual(report.generado_por, user)
        self.assertIn(report, user.reports.all())
