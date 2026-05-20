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
        self.assertTrue(dashboard.name)
        self.assertTrue(dashboard.description)
        self.assertIsInstance(dashboard.is_public, bool)
        self.assertIsNotNone(dashboard.owner)
        
    def test_dashboard_str_representation(self):
        """Test string representation of dashboard"""
        dashboard = DashboardFactory(name='Test Dashboard')
        self.assertEqual(str(dashboard), 'Test Dashboard')
        
    def test_dashboard_owner_relationship(self):
        """Test dashboard owner relationship"""
        user = UserFactory()
        dashboard = DashboardFactory(owner=user)
        self.assertEqual(dashboard.owner, user)
        self.assertIn(dashboard, user.dashboards.all())

class WidgetModelTest(TestCase):
    """Test cases for Widget model"""
    
    def test_widget_creation(self):
        """Test creating a widget"""
        widget = WidgetFactory()
        self.assertTrue(widget.title)
        self.assertIn(widget.widget_type, ['chart', 'table', 'metric', 'text'])
        self.assertGreaterEqual(widget.position_x, 0)
        self.assertLessEqual(widget.position_x, 11)
        self.assertGreaterEqual(widget.position_y, 0)
        self.assertLessEqual(widget.position_y, 10)
        self.assertGreaterEqual(widget.width, 1)
        self.assertLessEqual(widget.width, 4)
        self.assertGreaterEqual(widget.height, 1)
        self.assertLessEqual(widget.height, 3)
        self.assertIsNotNone(widget.dashboard)
        
    def test_widget_str_representation(self):
        """Test string representation of widget"""
        widget = WidgetFactory(title='Test Widget')
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
        self.assertTrue(report.title)
        self.assertTrue(report.description)
        self.assertIn(report.report_type, ['sales', 'inventory', 'users', 'operations'])
        self.assertIsNotNone(report.generated_by)
        self.assertIsInstance(report.parameters, dict)
        self.assertIsInstance(report.is_scheduled, bool)
        
    def test_report_str_representation(self):
        """Test string representation of report"""
        report = ReportFactory(title='Test Report')
        self.assertEqual(str(report), 'Test Report')
        
    def test_report_generator_relationship(self):
        """Test report generator relationship"""
        user = UserFactory()
        report = ReportFactory(generated_by=user)
        self.assertEqual(report.generated_by, user)
        self.assertIn(report, user.reports.all())